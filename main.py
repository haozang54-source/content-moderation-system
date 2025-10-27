"""应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="商业违规媒体智能审核系统",
    description="基于大模型的商业广告/直播违规内容智能审核系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/", tags=["健康检查"])
async def root():
    """根路径"""
    return {
        "message": "商业违规媒体智能审核系统",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
