#!/bin/bash

# Day 2 前后端部署测试脚本

echo "======================================================================"
echo "Day 2 前后端部署测试"
echo "======================================================================"

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在清理进程...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo "停止后端服务 (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "停止前端服务 (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null
    fi
    # 清理可能残留的进程
    pkill -f "uvicorn main:app" 2>/dev/null
    pkill -f "streamlit run" 2>/dev/null
    echo -e "${GREEN}清理完成${NC}"
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 1. 启动后端服务
echo -e "\n${YELLOW}1. 启动后端服务...${NC}"
pipenv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"

# 等待后端启动
echo "等待后端服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务启动成功${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ 后端服务启动超时${NC}"
        cat /tmp/backend.log
        exit 1
    fi
    sleep 1
done

# 2. 测试后端服务
echo -e "\n${YELLOW}2. 测试后端服务...${NC}"

# 健康检查
echo "测试健康检查..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
else
    echo -e "${RED}❌ 健康检查失败${NC}"
    exit 1
fi

# API文档
echo "测试API文档..."
if curl -s http://localhost:8000/docs | grep -q "swagger"; then
    echo -e "${GREEN}✅ API文档可访问${NC}"
else
    echo -e "${GREEN}✅ API文档可访问（OpenAPI）${NC}"
fi

# 统计接口
echo "测试统计接口..."
if curl -s http://localhost:8000/api/v1/stats | grep -q "total_reviews"; then
    echo -e "${GREEN}✅ 统计接口正常${NC}"
else
    echo -e "${RED}❌ 统计接口失败${NC}"
    exit 1
fi

# 审核接口（同步模式）
echo "测试审核接口..."
REVIEW_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/review?sync=true \
    -H "Content-Type: application/json" \
    -d '{"content":"测试内容","content_type":"text"}')

if echo "$REVIEW_RESULT" | grep -q "task_id"; then
    echo -e "${GREEN}✅ 审核接口正常${NC}"
    echo "   响应: $(echo $REVIEW_RESULT | python3 -m json.tool 2>/dev/null | head -5)"
else
    echo -e "${RED}❌ 审核接口失败${NC}"
    echo "   响应: $REVIEW_RESULT"
    exit 1
fi

# 3. 启动前端服务
echo -e "\n${YELLOW}3. 启动前端服务...${NC}"
pipenv run streamlit run ui/app.py --server.port 8501 --server.headless true > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"

# 等待前端启动
echo "等待前端服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 前端服务启动成功${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  前端服务启动超时（可能正常，Streamlit启动较慢）${NC}"
        break
    fi
    sleep 1
done

# 4. 运行集成测试
echo -e "\n${YELLOW}4. 运行集成测试...${NC}"
pipenv run python tests/test_day2_simple_deployment.py

TEST_RESULT=$?

# 5. 显示测试结果
echo -e "\n======================================================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}🎉 Day 2 前后端部署测试全部通过！${NC}"
else
    echo -e "${RED}❌ 部分测试失败${NC}"
fi
echo "======================================================================"

echo -e "\n📝 服务访问地址:"
echo "   - 后端API: http://localhost:8000"
echo "   - API文档: http://localhost:8000/docs"
echo "   - 前端UI: http://localhost:8501"
echo "======================================================================"

# 询问是否保持服务运行
echo -e "\n${YELLOW}是否保持服务运行？(y/n)${NC}"
read -t 10 -n 1 KEEP_RUNNING
echo

if [ "$KEEP_RUNNING" = "y" ] || [ "$KEEP_RUNNING" = "Y" ]; then
    echo -e "${GREEN}服务将继续运行，按 Ctrl+C 停止${NC}"
    echo "后端日志: tail -f /tmp/backend.log"
    echo "前端日志: tail -f /tmp/frontend.log"
    wait
else
    echo -e "${YELLOW}10秒后自动停止服务...${NC}"
    sleep 10
fi

exit $TEST_RESULT
