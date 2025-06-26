#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Monad RPC 优化器
基于真实测试结果的RPC调用优化和限流处理
"""

import asyncio
import logging
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass
from enum import Enum

class RPCErrorType(Enum):
    """RPC错误类型"""
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN = "unknown"

@dataclass
class RPCRequest:
    """RPC请求数据结构"""
    method: str
    params: List[Any]
    id: int
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def to_json(self) -> dict:
        return {
            "jsonrpc": "2.0",
            "method": self.method,
            "params": self.params,
            "id": self.id
        }

@dataclass
class RPCResponse:
    """RPC响应数据结构"""
    success: bool
    result: Any = None
    error: Any = None
    latency: float = 0
    retry_count: int = 0

class MonadRPCOptimizer:
    """Monad RPC优化器 - 基于真实测试结果优化"""
    
    def __init__(self, rpc_url: str, logger: logging.Logger = None):
        self.rpc_url = rpc_url
        self.logger = logger or logging.getLogger(__name__)
        
        # 基于测试结果的配置
        self.config = {
            'max_concurrent': 8,        # 最大并发数（测试验证的安全值）
            'batch_size': 100,          # 批量请求大小上限
            'timeout': 45,              # 请求超时时间
            'retry_attempts': 5,        # 重试次数
            'base_delay': 0.15,         # 基础延迟150ms
            'rate_limit_delay': 10,     # 遇到429时的延迟
            'max_retry_delay': 30,      # 最大重试延迟
            'circuit_breaker_threshold': 10,  # 熔断器阈值
        }
        
        # 运行时状态
        self.semaphore = Semaphore(self.config['max_concurrent'])
        self.session = self._create_session()
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0,
            'total_latency': 0,
            'circuit_breaker_trips': 0
        }
        
        # 熔断器状态
        self.circuit_breaker = {
            'is_open': False,
            'failure_count': 0,
            'last_failure_time': 0,
            'reset_timeout': 60  # 1分钟后尝试重置
        }
        
        # 缓存
        self.cache: Dict[str, Any] = {}
        self.cache_lock = Lock()
        
        self.logger.info(f"🚀 Monad RPC优化器初始化完成，最大并发: {self.config['max_concurrent']}")
    
    def _create_session(self) -> requests.Session:
        """创建优化的HTTP会话"""
        session = requests.Session()
        
        # 配置重试策略 - 专门针对Monad的问题
        retry_strategy = Retry(
            total=self.config['retry_attempts'],
            backoff_factor=2,  # 指数退避
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False
        )
        
        # 配置连接池
        adapter = HTTPAdapter(
            pool_connections=self.config['max_concurrent'],
            pool_maxsize=self.config['max_concurrent'] * 2,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认请求头
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Hemera-Indexer-Monad-Optimized/1.0'
        })
        
        return session
    
    def _check_circuit_breaker(self) -> bool:
        """检查熔断器状态"""
        if not self.circuit_breaker['is_open']:
            return True
        
        # 检查是否可以重置熔断器
        if (time.time() - self.circuit_breaker['last_failure_time'] > 
            self.circuit_breaker['reset_timeout']):
            self.circuit_breaker['is_open'] = False
            self.circuit_breaker['failure_count'] = 0
            self.logger.info("🔄 熔断器重置")
            return True
        
        return False
    
    def _update_circuit_breaker(self, success: bool):
        """更新熔断器状态"""
        if success:
            self.circuit_breaker['failure_count'] = 0
            if self.circuit_breaker['is_open']:
                self.circuit_breaker['is_open'] = False
                self.logger.info("✅ 熔断器关闭")
        else:
            self.circuit_breaker['failure_count'] += 1
            if (self.circuit_breaker['failure_count'] >= 
                self.config['circuit_breaker_threshold']):
                self.circuit_breaker['is_open'] = True
                self.circuit_breaker['last_failure_time'] = time.time()
                self.stats['circuit_breaker_trips'] += 1
                self.logger.warning(f"⚠️ 熔断器开启，连续失败: {self.circuit_breaker['failure_count']}")
    
    def _generate_cache_key(self, request: RPCRequest) -> str:
        """生成缓存键"""
        return f"{request.method}:{json.dumps(request.params, sort_keys=True)}"
    
    def _get_from_cache(self, request: RPCRequest) -> Optional[Any]:
        """从缓存获取结果"""
        cache_key = self._generate_cache_key(request)
        with self.cache_lock:
            return self.cache.get(cache_key)
    
    def _set_cache(self, request: RPCRequest, result: Any, ttl: int = 300):
        """设置缓存（TTL=5分钟）"""
        cache_key = self._generate_cache_key(request)
        with self.cache_lock:
            self.cache[cache_key] = {
                'result': result,
                'expires_at': time.time() + ttl
            }
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        with self.cache_lock:
            expired_keys = [
                key for key, value in self.cache.items()
                if value['expires_at'] < current_time
            ]
            for key in expired_keys:
                del self.cache[key]
    
    def _classify_error(self, response: requests.Response, exception: Exception = None) -> RPCErrorType:
        """分类错误类型"""
        if exception:
            if isinstance(exception, requests.Timeout):
                return RPCErrorType.TIMEOUT
            elif isinstance(exception, requests.ConnectionError):
                return RPCErrorType.CONNECTION
            else:
                return RPCErrorType.UNKNOWN
        
        if response.status_code == 429:
            return RPCErrorType.RATE_LIMIT
        elif response.status_code >= 500:
            return RPCErrorType.CONNECTION
        else:
            return RPCErrorType.INVALID_RESPONSE
    
    async def _make_single_request(self, request: RPCRequest) -> RPCResponse:
        """发送单个RPC请求"""
        # 检查熔断器
        if not self._check_circuit_breaker():
            return RPCResponse(
                success=False,
                error="Circuit breaker is open",
                latency=0
            )
        
        # 检查缓存
        cached_result = self._get_from_cache(request)
        if cached_result:
            return RPCResponse(
                success=True,
                result=cached_result['result'],
                latency=0
            )
        
        # 获取信号量
        await asyncio.sleep(0)  # 让出控制权
        self.semaphore.acquire()
        
        try:
            # 应用基础延迟
            if self.config['base_delay'] > 0:
                await asyncio.sleep(self.config['base_delay'])
            
            start_time = time.time()
            
            # 发送请求
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.post(
                    self.rpc_url,
                    json=request.to_json(),
                    timeout=self.config['timeout']
                )
            )
            
            latency = time.time() - start_time
            self.stats['total_requests'] += 1
            self.stats['total_latency'] += latency
            
            # 处理响应
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if 'result' in json_response:
                        # 成功响应
                        self.stats['successful_requests'] += 1
                        self._update_circuit_breaker(True)
                        
                        # 缓存结果
                        self._set_cache(request, json_response['result'])
                        
                        return RPCResponse(
                            success=True,
                            result=json_response['result'],
                            latency=latency
                        )
                    else:
                        # RPC错误
                        self.stats['failed_requests'] += 1
                        self._update_circuit_breaker(False)
                        return RPCResponse(
                            success=False,
                            error=json_response.get('error', 'Unknown RPC error'),
                            latency=latency
                        )
                except json.JSONDecodeError:
                    self.stats['failed_requests'] += 1
                    self._update_circuit_breaker(False)
                    return RPCResponse(
                        success=False,
                        error="Invalid JSON response",
                        latency=latency
                    )
            else:
                # HTTP错误
                error_type = self._classify_error(response)
                if error_type == RPCErrorType.RATE_LIMIT:
                    self.stats['rate_limited_requests'] += 1
                    # 遇到429时等待更长时间
                    await asyncio.sleep(self.config['rate_limit_delay'])
                
                self.stats['failed_requests'] += 1
                self._update_circuit_breaker(False)
                return RPCResponse(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    latency=latency
                )
                
        except Exception as e:
            self.stats['failed_requests'] += 1
            self._update_circuit_breaker(False)
            latency = time.time() - start_time
            return RPCResponse(
                success=False,
                error=str(e),
                latency=latency
            )
        finally:
            self.semaphore.release()
    
    async def batch_request(self, requests_list: List[RPCRequest]) -> List[RPCResponse]:
        """批量发送RPC请求"""
        if not requests_list:
            return []
        
        self.logger.debug(f"📦 批量处理 {len(requests_list)} 个请求")
        
        # 分批处理（基于测试结果的批量大小）
        results = []
        for i in range(0, len(requests_list), self.config['batch_size']):
            batch = requests_list[i:i + self.config['batch_size']]
            
            # 并发发送批次内的请求
            tasks = [self._make_single_request(req) for req in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # 批次间短暂延迟
            if i + self.config['batch_size'] < len(requests_list):
                await asyncio.sleep(0.1)
        
        # 定期清理缓存
        if self.stats['total_requests'] % 1000 == 0:
            self._cleanup_cache()
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_requests = self.stats['total_requests']
        if total_requests == 0:
            return self.stats.copy()
        
        stats = self.stats.copy()
        stats['success_rate'] = self.stats['successful_requests'] / total_requests
        stats['error_rate'] = self.stats['failed_requests'] / total_requests
        stats['avg_latency'] = self.stats['total_latency'] / total_requests
        stats['cache_size'] = len(self.cache)
        
        return stats
    
    def log_stats(self):
        """记录性能统计"""
        stats = self.get_stats()
        self.logger.info(
            f"📊 RPC统计 - "
            f"总请求: {stats['total_requests']}, "
            f"成功率: {stats.get('success_rate', 0):.2%}, "
            f"平均延迟: {stats.get('avg_latency', 0):.3f}s, "
            f"缓存大小: {stats['cache_size']}, "
            f"限流次数: {stats['rate_limited_requests']}"
        )

# 便捷函数
async def optimized_rpc_call(rpc_url: str, method: str, params: List[Any], 
                           request_id: int = 1) -> RPCResponse:
    """优化的单次RPC调用"""
    optimizer = MonadRPCOptimizer(rpc_url)
    request = RPCRequest(method=method, params=params, id=request_id)
    return await optimizer._make_single_request(request)

async def optimized_batch_rpc_call(rpc_url: str, requests_data: List[Tuple[str, List[Any]]], 
                                 logger: logging.Logger = None) -> List[RPCResponse]:
    """优化的批量RPC调用"""
    optimizer = MonadRPCOptimizer(rpc_url, logger)
    requests = [
        RPCRequest(method=method, params=params, id=i)
        for i, (method, params) in enumerate(requests_data)
    ]
    return await optimizer.batch_request(requests)