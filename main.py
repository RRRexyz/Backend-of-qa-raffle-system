from fastapi import FastAPI
from routers import helloworld, login, qa
from sql.database import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware



tags_metadata = [
    {
        "name": "测试",
        "description": "没啥用。"
    },
    {
        "name": "用户模块",
        "description": "用于用户注册、登录、注销的API，包括token生成和验证。"
    },
    {
        "name": "项目模块",
        "description": "用于增删查改项目相关内容的API，包括问答和抽奖。"
    }
]


app = FastAPI(title="问答抽奖系统", version="0.0.1", 
            openapi_tags=tags_metadata)


app.include_router(helloworld.router, tags=["测试"])
app.include_router(login.router, tags=["用户模块"], prefix="/api")
app.include_router(qa.router, tags=["项目模块"], prefix="/api")


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
    
    

