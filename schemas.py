from pydantic import BaseModel
import datetime

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

    
class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    create_time: datetime.datetime
    deadline: datetime.datetime
    status: int
    creater_id: int
    
    
class QuestionCreate(BaseModel):
    question: str
    answer: int