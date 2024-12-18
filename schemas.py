from pydantic import BaseModel
import datetime
from sqlmodel import SQLModel


class UserRegister(BaseModel):
    username: str
    password: str
    qq: str 
    phone: str
    manage_permission: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "rex",
                "password": "111",
                "qq": "2467945786",
                "phone": "13812345678",
                "manage_permission": False
            }
        }
    }
    
    
class UserLogin(BaseModel):
    username: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "rex",
                "password": "111",
            }
        }
    }
    
    
class UserResponse(BaseModel):
    id: int
    username: str
    manage_permission: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "rex",
                "manage_permission": False,
            }
        }
    }    
    
    
class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    deadline: datetime.datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "校史问答",
                "description": "关于山东大学历史的问答及抽奖活动",
                "deadline": "2025-01-01T00:00:00"
            }
        }
    }

    
class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    create_time: datetime.datetime
    deadline: datetime.datetime
    status: int
    browse_times: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "校史问答",
                "description": "关于山东大学历史的问答及抽奖活动",
                "create_time": "2024-12-12 22:43:41.957805",
                "deadline": "2025-01-01 00:00:00.000000",
                "status": 0,
                "browse_times": 0
            }
        }
    }
    
    
class QuestionAdd(BaseModel):
    project_id: int
    q: str
    a: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": 1,
                "q": "山东大学在哪一年建校？",
                "a": 3
            }
        }
    }
    

class QuestionResponse(BaseModel):
    project_id: int
    id: int
    q: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": 1,
                "id": 1,
                "q": "山东大学在哪一年建校？",
            }
        }
    }



class ProjectPublic(SQLModel):
    id: int
    name: str
    description: str | None = None
    create_time: datetime.datetime
    deadline: datetime.datetime
    status: int
    browse_times: int


class QuestionPublic(SQLModel):
    id: int
    q: str

    
class ProjectWithQuestions(ProjectPublic):
    question: list[QuestionPublic] = []
    
    model_config = {
        "json_schema_extra": {
            "example": 
                    {
                        "id": 1,
                        "name": "校史问答",
                        "description": "关于山东大学历史的问答及抽奖活动",
                        "create_time": "2024-12-12T22:43:41.957805",
                        "deadline": "2025-01-01T00:00:00",
                        "status": 0,
                        "browse_times": 0,
                        "question": [
                        {
                            "id": 1,
                            "q": "山东大学在哪一年建校？",
                        },
                        {
                            "id": 2,
                            "q": "兴隆山校区在哪一年建成？",
                        }
                    ]
                }
            }
        }


class PrizeAdd(BaseModel):
    name: str
    image: str | None = None
    level: int | None = None
    amount: int
    probability: float
    project_id: int