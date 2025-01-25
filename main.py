from fastapi import FastAPI
from sql.database import create_db_and_tables
from routers import admin, backstage, frontstage
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


tags_metadata = [
    {
        "name": "用户模块",
        "description": "管理员账户的注册、登录、注销和用户鉴权。"
    },
    {
        "name": "后台管理端",
        "description": "管理员增删查改项目相关内容。"
    },
    {
        "name": "前台用户端",
        "description": "用户参与问答抽奖项目。"
    }
]


app = FastAPI(title="问答抽奖系统", version="0.1.0", 
            openapi_tags=tags_metadata)


app.include_router(admin.router, tags=["用户模块"], prefix="/api")
app.include_router(backstage.router, tags=["后台管理端"], prefix="/api")
app.include_router(frontstage.router, tags=["前台用户端"], prefix="/api")


app.mount("/static", StaticFiles(directory="./static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    create_db_and_tables()
    import uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
    