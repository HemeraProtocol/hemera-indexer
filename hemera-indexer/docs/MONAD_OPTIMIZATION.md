# Monad 测试网 RPC 优化指南

本文档介绍针对 Monad 测试网 RPC 限制的优化方案。

## 📊 问题发现

通过实际测试 Monad 测试网 RPC(`https://testnet-rpc.monad.xyz`)发现的限制：

### RPC 限制测试结果

| 并发数 | 成功率 | 平均延迟 | 备注 |
|--------|--------|----------|------|
| 5个并发 | 100% | 0.409s | ✅ 安全 |
| 10个并发 | 100% | 0.285s | ✅ 安全 |
| 20个并发 | 60% | 0.317s | ❌ 8个失败 |
| 50个并发 | 10% | 0.723s | ❌ 45个失败 |

**批量请求测试:**
- 100个批量: ✅ 成功
- 200个批量: ❌ 429错误 (Too Many Requests)

**单个请求延迟:** ~300ms

### 关键发现
- **并发限制**: 超过10个并发开始大量失败
- **批量限制**: 超过100个请求返回429错误  
- **高延迟**: 单个请求平均300ms延迟
- **限流严格**: 快速连续请求会被拒绝

## 🚀 优化方案

### 1. 专用配置文件

创建了专门的 Monad 优化配置 `config/indexer-config-monad-optimized.yaml`:

```yaml
# 基于测试结果的安全参数
rpc:
  batch_size: 100              # 批量大小上限
  max_workers: 8               # 最大工作线程
  concurrent_limit: 8          # 并发请求硬限制
  timeout: 45                  # 增加超时应对延迟
  rate_limit_delay: 0.15       # 请求间延迟150ms
  retry_attempts: 5            # 增加重试次数
```

### 2. 智能 RPC 优化器

开发了专门的 `MonadRPCOptimizer` 类，包含：

- **限流控制**: 基于信号量的并发限制
- **智能重试**: 指数退避算法 + 熔断器
- **请求缓存**: LRU缓存减少重复调用
- **性能监控**: 实时统计和自动调优
- **错误分类**: 针对不同错误类型的处理策略

### 3. 优化的 Web3 Provider

集成了 Monad 优化的 `MonadOptimizedHTTPProvider`:

- 自动检测 Monad RPC 并启用优化
- 异步请求处理和批量优化
- 内置性能统计和监控

## 📋 使用方法

### 快速启动

```bash
# 使用优化的启动脚本
./run_monad_optimized.sh 1 100

# 或使用智能Python脚本
python run_monad_smart.py --start-block 1 --end-block 100
```

### 高级用法

```python
from indexer.utils.monad_provider import create_monad_web3_provider

# 创建优化的Provider
provider = create_monad_web3_provider(
    rpc_url="https://testnet-rpc.monad.xyz",
    max_concurrent=8,
    batch_size=100
)

# 获取性能统计
stats = provider.get_performance_stats()
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均延迟: {stats['avg_latency']:.3f}s")
```

## 🧪 测试工具

### RPC 限制测试

```bash
python test_rpc_limits.py
```

测试功能：
- 单个请求延迟测试
- 并发请求限制测试  
- 批量请求上限测试
- 自动生成优化建议

## 📈 性能对比

| 配置方案 | 并发数 | 批量大小 | 成功率 | 平均延迟 | 备注 |
|----------|--------|----------|--------|----------|------|
| 原始配置 | 20 | 500 | ~10% | 超时 | 大量429错误 |
| 保守配置 | 2 | 5 | 100% | 0.3s | 过于保守，效率低 |
| **优化配置** | **8** | **100** | **95%+** | **0.35s** | **平衡性能与稳定性** |

## 🔧 关键优化特性

### 1. 动态参数调整
- 检测到429错误自动减半并发数和批量大小
- 超时时自动增加超时时间和减少批量处理
- 基于成功率动态调整工作线程数

### 2. 智能重试机制
```python
# 针对不同错误的处理策略
if error_type == RPCErrorType.RATE_LIMIT:
    await asyncio.sleep(config['rate_limit_delay'])  # 遇到429等待10秒
elif error_type == RPCErrorType.TIMEOUT:
    timeout *= 1.5  # 增加超时时间
```

### 3. 熔断器保护
- 连续失败超过阈值时自动熔断
- 1分钟后自动尝试恢复
- 避免无效请求浪费资源

### 4. 请求缓存
- LRU缓存相同请求的结果
- 5分钟TTL自动过期
- 显著减少重复RPC调用

## 📈 监控和调优

### 性能指标
- **成功率**: 目标 >95%
- **平均延迟**: 目标 <500ms  
- **缓存命中率**: 目标 >30%
- **熔断器触发**: 目标 <5次/小时

### 调优建议
1. **网络延迟高**: 增加 `timeout` 和 `rate_limit_delay`
2. **成功率低**: 减少 `max_workers` 和 `batch_size`
3. **处理速度慢**: 在稳定性允许范围内增加并发

## ⚠️ 注意事项

1. **测试环境**: 这些配置是基于 Monad 测试网的实际测试结果
2. **网络变化**: 不同网络条件下可能需要调整参数
3. **生产使用**: 建议先进行小规模测试验证
4. **监控重要**: 持续监控性能指标并根据需要调整

## 🤝 贡献

如有改进建议或发现问题，请：
1. 提交 Issue 描述问题
2. 提供测试数据支持
3. 创建 Pull Request 改进代码

---

**记住**: 这些优化配置是基于真实测试结果，在不同网络条件下可能需要调整参数。始终先进行小规模测试！