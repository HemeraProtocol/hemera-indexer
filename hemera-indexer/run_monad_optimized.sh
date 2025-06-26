#!/bin/bash
# Monad 测试网优化索引器启动脚本
# 基于RPC限制测试结果的最优配置

set -e

echo "🚀 启动 Monad 测试网优化索引器"
echo "================================="

# 配置参数
MONAD_RPC="https://testnet-rpc.monad.xyz"
POSTGRES_URI="postgresql://devuser:hemera123@localhost:5432/hemera_indexer"
CONFIG_FILE="config/indexer-config-monad-optimized.yaml"

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 检查数据库连接
echo "🔍 检查数据库连接..."
if ! python -c "import psycopg2; psycopg2.connect('$POSTGRES_URI')" 2>/dev/null; then
    echo "❌ 数据库连接失败，请检查 PostgreSQL 服务"
    exit 1
fi

# 检查RPC连接
echo "🔍 检查 Monad RPC 连接..."
if ! curl -s -f -X POST -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    "$MONAD_RPC" > /dev/null; then
    echo "❌ Monad RPC 连接失败"
    exit 1
fi

echo "✅ 预检查通过"

# 获取最新区块
LATEST_BLOCK=$(curl -s -X POST -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    "$MONAD_RPC" | python -c "import sys, json; print(int(json.load(sys.stdin)['result'], 16))")

echo "📊 当前最新区块: $LATEST_BLOCK"

# 设置起始和结束区块
START_BLOCK=${1:-1}
END_BLOCK=${2:-100}

if [ "$END_BLOCK" -gt "$LATEST_BLOCK" ]; then
    END_BLOCK=$LATEST_BLOCK
    echo "⚠️  调整结束区块为最新区块: $END_BLOCK"
fi

echo "📋 索引范围: $START_BLOCK - $END_BLOCK"

# 优化的索引器参数（基于RPC限制测试）
INDEXER_PARAMS=(
    "stream"
    "--provider-uri" "$MONAD_RPC"
    "--debug-provider-uri" "$MONAD_RPC"
    "--output" "postgres+$POSTGRES_URI"
    "--start-block" "$START_BLOCK"
    "--end-block" "$END_BLOCK"
    "--config" "$CONFIG_FILE"
    
    # 核心优化参数
    "--entity-types" "block,transaction,log,token_transfer,trace,contract"
    "--block-batch-size" "30"          # 基于测试的安全值
    "--batch-size" "100"               # RPC批量调用上限
    "--max-workers" "8"                # 并发工作线程
    
    # 性能和稳定性参数
    "--timeout" "45"                   # 增加超时应对延迟
    "--retry-attempts" "5"             # 增加重试次数
    "--retry-delay" "2"                # 重试延迟
    
    # 日志和监控
    "--log-level" "INFO"
    "--enable-performance-logging"
    "--log-rpc-calls"                  # 启用RPC调用日志
    
    # 内存和资源管理
    "--max-memory-usage" "2GB"
    "--enable-memory-monitoring"
)

echo "🔧 启动参数:"
for param in "${INDEXER_PARAMS[@]}"; do
    echo "   $param"
done

echo ""
echo "🚀 开始索引 Monad 测试网数据..."
echo "================================="

# 启动索引器，包含错误处理
python hemera.py "${INDEXER_PARAMS[@]}" || {
    echo "❌ 索引器执行失败"
    echo "💡 可能的原因:"
    echo "   - RPC连接超时或限制"
    echo "   - 数据库写入错误"
    echo "   - 内存不足"
    echo ""
    echo "🔧 建议操作:"
    echo "   - 减少批量大小和工作线程数"
    echo "   - 检查 RPC 连接稳定性"
    echo "   - 查看详细日志排错"
    exit 1
}

echo ""
echo "✅ Monad 索引器执行完成!"
echo "📊 数据范围: 区块 $START_BLOCK - $END_BLOCK"
echo "🔍 可通过 API 或数据库查询索引结果"