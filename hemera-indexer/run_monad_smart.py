#!/usr/bin/env python3
"""
智能化 Monad 索引器启动脚本
基于RPC限制测试结果，动态调整参数，自动重试机制
"""

import argparse
import logging
import os
import sys
import time
import subprocess
import requests
import json
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'monad_indexer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MonadIndexerOptimized:
    """优化的 Monad 索引器"""
    
    def __init__(self):
        self.rpc_url = "https://testnet-rpc.monad.xyz"
        self.postgres_uri = "postgresql://devuser:hemera123@localhost:5432/hemera_indexer"
        self.config_file = "config/indexer-config-monad-optimized.yaml"
        
        # 基于测试结果的参数
        self.optimal_params = {
            'batch_size': 100,
            'max_workers': 8,
            'block_batch_size': 30,
            'timeout': 45,
            'retry_attempts': 5,
            'retry_delay': 2
        }
        
        # 动态调整参数
        self.current_params = self.optimal_params.copy()
        self.performance_stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'avg_latency': 0,
            'error_rate': 0
        }
    
    def test_rpc_connection(self):
        """测试RPC连接和性能"""
        logger.info("🔍 测试 Monad RPC 连接...")
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 1
        }
        
        try:
            start_time = time.time()
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                latest_block = int(result['result'], 16)
                logger.info(f"✅ RPC连接成功, 最新区块: {latest_block}, 延迟: {latency:.3f}s")
                return True, latest_block, latency
            else:
                logger.error(f"❌ RPC连接失败, 状态码: {response.status_code}")
                return False, 0, 0
                
        except Exception as e:
            logger.error(f"❌ RPC连接异常: {e}")
            return False, 0, 0
    
    def test_concurrent_performance(self):
        """测试并发性能并动态调整参数"""
        logger.info("🧪 测试并发性能...")
        
        import asyncio
        import aiohttp
        
        async def test_concurrent_requests(concurrent_count):
            """异步测试并发请求"""
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
            
            async def make_request(session, request_id):
                try:
                    start = time.time()
                    async with session.post(self.rpc_url, json={**payload, "id": request_id}) as response:
                        latency = time.time() - start
                        return {"success": response.status == 200, "latency": latency}
                except Exception:
                    return {"success": False, "latency": 0}
            
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, i) for i in range(concurrent_count)]
                results = await asyncio.gather(*tasks)
            
            return results
        
        # 测试不同并发级别
        for concurrent in [5, 8, 10, 15]:
            results = asyncio.run(test_concurrent_requests(concurrent))
            successful = [r for r in results if r['success']]
            success_rate = len(successful) / len(results)
            
            logger.info(f"   并发 {concurrent}: 成功率 {success_rate:.2%}")
            
            if success_rate >= 0.95:  # 95%成功率
                self.current_params['max_workers'] = concurrent
            else:
                break
        
        logger.info(f"📊 动态调整后的最大工作线程: {self.current_params['max_workers']}")
    
    def check_database_connection(self):
        """检查数据库连接"""
        logger.info("🔍 检查数据库连接...")
        
        try:
            import psycopg2
            conn = psycopg2.connect(self.postgres_uri)
            conn.close()
            logger.info("✅ 数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False
    
    def build_indexer_command(self, start_block, end_block):
        """构建索引器命令"""
        cmd = [
            sys.executable, "hemera.py", "stream",
            "--provider-uri", self.rpc_url,
            "--debug-provider-uri", self.rpc_url,
            "--output", f"postgres+{self.postgres_uri}",
            "--start-block", str(start_block),
            "--end-block", str(end_block),
            "--config", self.config_file,
            
            # 动态调整的参数
            "--entity-types", "block,transaction,log,token_transfer,trace,contract",
            "--block-batch-size", str(self.current_params['block_batch_size']),
            "--batch-size", str(self.current_params['batch_size']),
            "--max-workers", str(self.current_params['max_workers']),
            "--timeout", str(self.current_params['timeout']),
            "--retry-attempts", str(self.current_params['retry_attempts']),
            "--retry-delay", str(self.current_params['retry_delay']),
            
            # 监控和日志
            "--log-level", "INFO",
            "--enable-performance-logging",
            "--log-rpc-calls"
        ]
        
        return cmd
    
    def run_indexer_with_retry(self, start_block, end_block, max_retries=3):
        """运行索引器，包含智能重试机制"""
        logger.info(f"🚀 开始索引区块 {start_block} - {end_block}")
        
        for attempt in range(max_retries):
            try:
                cmd = self.build_indexer_command(start_block, end_block)
                logger.info(f"📋 尝试 {attempt + 1}/{max_retries}")
                
                # 执行命令
                process = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                
                if process.returncode == 0:
                    logger.info("✅ 索引器执行成功")
                    return True
                else:
                    logger.error(f"❌ 索引器执行失败，返回码: {process.returncode}")
                    logger.error(f"错误输出: {process.stderr}")
                    
                    # 根据错误调整参数
                    if "429" in process.stderr or "rate limit" in process.stderr.lower():
                        self.adjust_params_for_rate_limit()
                    elif "timeout" in process.stderr.lower():
                        self.adjust_params_for_timeout()
                    
            except subprocess.TimeoutExpired:
                logger.error("❌ 索引器执行超时")
                self.adjust_params_for_timeout()
            except Exception as e:
                logger.error(f"❌ 索引器执行异常: {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        return False
    
    def adjust_params_for_rate_limit(self):
        """调整参数应对速率限制"""
        logger.info("🔧 检测到速率限制，调整参数...")
        self.current_params['batch_size'] = max(50, self.current_params['batch_size'] // 2)
        self.current_params['max_workers'] = max(2, self.current_params['max_workers'] // 2)
        self.current_params['retry_delay'] = min(10, self.current_params['retry_delay'] * 2)
        logger.info(f"   调整后参数: batch_size={self.current_params['batch_size']}, "
                   f"max_workers={self.current_params['max_workers']}, "
                   f"retry_delay={self.current_params['retry_delay']}")
    
    def adjust_params_for_timeout(self):
        """调整参数应对超时"""
        logger.info("🔧 检测到超时，调整参数...")
        self.current_params['timeout'] = min(120, self.current_params['timeout'] * 1.5)
        self.current_params['block_batch_size'] = max(10, self.current_params['block_batch_size'] // 2)
        logger.info(f"   调整后参数: timeout={self.current_params['timeout']}, "
                   f"block_batch_size={self.current_params['block_batch_size']}")
    
    def run(self, start_block=1, end_block=100):
        """主执行函数"""
        logger.info("🚀 智能化 Monad 索引器启动")
        logger.info("=" * 50)
        
        # 预检查
        rpc_ok, latest_block, latency = self.test_rpc_connection()
        if not rpc_ok:
            logger.error("❌ RPC连接失败，退出")
            return False
        
        if not self.check_database_connection():
            logger.error("❌ 数据库连接失败，退出")
            return False
        
        # 动态调整参数
        self.test_concurrent_performance()
        
        # 调整结束区块
        if end_block > latest_block:
            end_block = latest_block
            logger.info(f"⚠️ 调整结束区块为最新区块: {end_block}")
        
        # 分批处理大范围区块
        chunk_size = 1000  # 每批处理1000个区块
        current_start = start_block
        
        while current_start <= end_block:
            current_end = min(current_start + chunk_size - 1, end_block)
            
            success = self.run_indexer_with_retry(current_start, current_end)
            if not success:
                logger.error(f"❌ 区块 {current_start}-{current_end} 索引失败")
                return False
            
            current_start = current_end + 1
            
            # 短暂休息避免过载
            if current_start <= end_block:
                time.sleep(5)
        
        logger.info("✅ 所有区块索引完成")
        return True

def main():
    parser = argparse.ArgumentParser(description="智能化 Monad 索引器")
    parser.add_argument("--start-block", type=int, default=1, help="起始区块号")
    parser.add_argument("--end-block", type=int, default=100, help="结束区块号")
    
    args = parser.parse_args()
    
    indexer = MonadIndexerOptimized()
    success = indexer.run(args.start_block, args.end_block)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()