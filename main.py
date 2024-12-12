from fastapi import FastAPI
from routers import helloworld, login, qa
from sql.database import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware



tags_metadata = [
    {
        "name": "HelloWorld",
        "description": "No usage."
    },
    {
        "name": "Login",
        "description": "APIs for users to register and login, including token generation and verification."
    },
    {
        "name": "QA",
        "description": "APIs for users to curd Q&A projects and answer questions."
    }
]

summary = """
This is a system for Student Online members to create Q&A projects and provide prizes for 
answerers to raffle.
"""

app = FastAPI(title="QA Raffle System", version="0.0.0", 
            openapi_tags=tags_metadata, summary=summary)


app.include_router(helloworld.router, tags=["HelloWorld"])
app.include_router(login.router, tags=["Login"], prefix="/api")
app.include_router(qa.router, tags=["QA"], prefix="/api")


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
    
    

