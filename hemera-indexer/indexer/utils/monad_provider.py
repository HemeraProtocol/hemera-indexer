#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Monad 优化的 Web3 Provider
集成RPC限制处理和智能重试机制
"""

import logging
import time
import asyncio
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from web3 import HTTPProvider
from web3._utils.request import make_post_request
from web3.types import RPCEndpoint

from .monad_rpc_optimizer import MonadRPCOptimizer, RPCRequest, RPCResponse

logger = logging.getLogger(__name__)

class MonadOptimizedHTTPProvider(HTTPProvider):
    """Monad优化的HTTP Provider"""
    
    def __init__(self, endpoint_uri: str, request_kwargs: Optional[Dict[str, Any]] = None, 
                 optimizer_config: Optional[Dict[str, Any]] = None):
        super().__init__(endpoint_uri, request_kwargs)
        
        # 初始化Monad优化器
        self.optimizer = MonadRPCOptimizer(endpoint_uri, logger)
        
        # 应用优化配置
        if optimizer_config:
            self.optimizer.config.update(optimizer_config)
        
        # 性能监控
        self.request_count = 0
        self.last_stats_log = time.time()
        self.stats_log_interval = 300  # 5分钟记录一次统计
        
        logger.info(f"🚀 Monad优化Provider初始化: {endpoint_uri}")
    
    def make_request(self, method: RPCEndpoint, params: Any) -> Any:
        """发送RPC请求（同步接口）"""
        # 将同步调用转换为异步
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 如果事件循环正在运行，使用 run_coroutine_threadsafe
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(
                self._async_make_request(method, params), loop
            )
            return future.result(timeout=self.optimizer.config['timeout'])
        else:
            # 如果事件循环未运行，直接运行
            return loop.run_until_complete(self._async_make_request(method, params))
    
    async def _async_make_request(self, method: RPCEndpoint, params: Any) -> Any:
        """异步发送RPC请求"""
        self.request_count += 1
        
        # 创建RPC请求
        rpc_request = RPCRequest(
            method=method,
            params=params if isinstance(params, list) else [params] if params else [],
            id=self.request_count
        )
        
        # 发送请求
        response = await self.optimizer._make_single_request(rpc_request)
        
        # 记录统计信息
        self._log_stats_if_needed()
        
        if response.success:
            return response.result
        else:
            # 根据错误类型抛出不同异常
            error_msg = f"RPC request failed: {response.error}"
            if "429" in str(response.error) or "rate limit" in str(response.error).lower():
                raise Exception(f"Rate limit exceeded: {response.error}")
            elif "timeout" in str(response.error).lower():
                raise Exception(f"Request timeout: {response.error}")
            else:
                raise Exception(error_msg)
    
    def batch_make_request(self, requests: List[tuple]) -> List[Any]:
        """批量发送RPC请求"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(
                self._async_batch_make_request(requests), loop
            )
            return future.result(timeout=self.optimizer.config['timeout'] * 2)
        else:
            return loop.run_until_complete(self._async_batch_make_request(requests))
    
    async def _async_batch_make_request(self, requests: List[tuple]) -> List[Any]:
        """异步批量发送RPC请求"""
        # 转换为RPC请求对象
        rpc_requests = []
        for i, (method, params) in enumerate(requests):
            rpc_request = RPCRequest(
                method=method,
                params=params if isinstance(params, list) else [params] if params else [],
                id=self.request_count + i + 1
            )
            rpc_requests.append(rpc_request)
        
        self.request_count += len(rpc_requests)
        
        # 发送批量请求
        responses = await self.optimizer.batch_request(rpc_requests)
        
        # 记录统计信息
        self._log_stats_if_needed()
        
        # 处理响应
        results = []
        for response in responses:
            if response.success:
                results.append(response.result)
            else:
                # 对于批量请求，失败的项目返回None或抛出异常
                logger.warning(f"Batch request item failed: {response.error}")
                results.append(None)
        
        return results
    
    def _log_stats_if_needed(self):
        """根据需要记录统计信息"""
        current_time = time.time()
        if current_time - self.last_stats_log > self.stats_log_interval:
            self.optimizer.log_stats()
            self.last_stats_log = current_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.optimizer.get_stats()
    
    def reset_stats(self):
        """重置统计信息"""
        self.optimizer.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0,
            'total_latency': 0,
            'circuit_breaker_trips': 0
        }
        self.request_count = 0

def get_monad_provider_from_uri(uri_string: str, timeout: int = 60, 
                               optimizer_config: Optional[Dict[str, Any]] = None,
                               batch: bool = False) -> Union[MonadOptimizedHTTPProvider, HTTPProvider]:
    """
    创建Monad优化的Provider
    
    Args:
        uri_string: RPC端点URI
        timeout: 请求超时时间
        optimizer_config: 优化器配置
        batch: 是否使用批量模式
    
    Returns:
        优化的Provider实例
    """
    uri = urlparse(uri_string)
    
    if uri.scheme in ["http", "https"]:
        request_kwargs = {"timeout": timeout}
        
        # 检查是否是Monad RPC
        if "monad" in uri_string.lower():
            logger.info("🎯 检测到Monad RPC，使用优化Provider")
            return MonadOptimizedHTTPProvider(
                uri_string, 
                request_kwargs=request_kwargs,
                optimizer_config=optimizer_config
            )
        else:
            # 对于非Monad RPC，使用标准Provider
            return HTTPProvider(uri_string, request_kwargs=request_kwargs)
    else:
        raise ValueError(f"Unsupported URI scheme for Monad provider: {uri.scheme}")

# 便捷函数
def create_monad_web3_provider(rpc_url: str = "https://testnet-rpc.monad.xyz",
                              max_concurrent: int = 8,
                              batch_size: int = 100) -> MonadOptimizedHTTPProvider:
    """
    创建Monad Web3 Provider的便捷函数
    
    Args:
        rpc_url: Monad RPC URL
        max_concurrent: 最大并发数
        batch_size: 批量大小
    
    Returns:
        配置好的Monad Provider
    """
    optimizer_config = {
        'max_concurrent': max_concurrent,
        'batch_size': batch_size,
    }
    
    return get_monad_provider_from_uri(
        rpc_url, 
        timeout=45,
        optimizer_config=optimizer_config
    )