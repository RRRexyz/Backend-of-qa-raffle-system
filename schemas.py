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
                "deadline": "2025-01-01 00:00:00"
            }
        }
    }


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    deadline: datetime.datetime | None = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "校史问答",
                "description": "关于山东大学历史的问答及抽奖活动",
                "deadline": "2025-01-01 00:00:00"
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
                "create_time": "2024-12-12T22:43:41.957805",
                "deadline": "2025-01-01T00:00:00",
                "status": 0,
                "browse_times": 0
            }
        }
    }
    
    
class QuestionAdd(BaseModel):
    project_id: int
    q: str
    o1: str
    o2: str
    o3: str
    o4: str
    a: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": 1,
                "q": "山东大学在哪一年建校？",
                "o1": "1899",
                "o2": "1900",
                "o3": "1901",
                "o4": "1902",
                "a": 3
            }
        }
    }
    
    
class QuestionUpdate(BaseModel):
    q: str | None = None
    o1: str | None = None
    o2: str | None = None
    o3: str | None = None
    o4: str | None = None
    a: int | None = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "q": "山东大学在哪一年建校？",
                "o1": "1899",
                "o2": "1900",
                "o3": "1901",
                "o4": "1902",
                "a": 3
            }
        }
    }


class QuestionResponse(BaseModel):
    project_id: int
    id: int
    q: str
    o1: str
    o2: str
    o3: str
    o4: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": 1,
                "id": 1,
                "q": "山东大学在哪一年建校？",
                "o1": "1899",
                "o2": "1900",
                "o3": "1901",
                "o4": "1902"
            }
        }
    }


class PrizeAdd(BaseModel):
    name: str
    image: str | None = None
    level: int | None = None
    amount: int
    project_id: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "手机支架",
                "image": "https://dummyimage.com/400x300",
                "level": 2,
                "amount": 20,
                "project_id": 1
            }
        }
    }
    

class PrizeUpdate(BaseModel):
    name: str | None = None
    image: str | None = None
    level: int | None = None
    amount: int | None = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "手机支架",
                "image": "https://dummyimage.com/400x300",
                "level": 2,
                "amount": 20
            }
        }
    }


class PrizeResponse(BaseModel):
    id: int
    name: str
    image: str | None = None
    level: int | None = None
    amount: int
    remain: int
    project_id: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "手机支架",
                "image": "https://dummyimage.com/400x300",
                "level": 2,
                "amount": 20,
                "remain": 20,
                "project_id": 1
            }
        }
    }


class UserPublic(SQLModel):
    id: int
    username: str


class ProjectPublic(SQLModel):
    id: int
    name: str
    description: str | None = None
    create_time: datetime.datetime
    deadline: datetime.datetime
    status: int
    browse_times: int
    creater: UserPublic


class QuestionPublicWithoutAnswer(SQLModel):
    id: int
    q: str
    o1: str
    o2: str
    o3: str
    o4: str
    
class QuestionPublicWithAnswer(QuestionPublicWithoutAnswer):
    a: int


class PrizePublic(SQLModel):
    id: int
    name: str
    image: str | None = None
    level: int | None = None
    amount: int
    remain: int
    project_id: int

    
class ProjectWithQuestionsAndPrizesForUser(ProjectPublic):
    question: list[QuestionPublicWithoutAnswer] = []    
    user_answer: list[int] = []
    correct_answer: list[int] = []
    prize: list[PrizePublic] = []
    raffle_times: int | None = None
    raffle_result: list[int] = []
    raffle_remain_times: int | None = None
    raffle_time: datetime.datetime | None = None
    
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
                        "creater": {
                            "id": 1,
                            "username": "rexyz"
                        },
                        "question": [
                        {
                            "id": 1,
                            "q": "山东大学在哪一年建校？",
                            "o1": "1899",
                            "o2": "1900",
                            "o3": "1901",
                            "o4": "1902"
                        },
                        {
                            "id": 2,
                            "q": "兴隆山校区在哪一年建成？",
                            "o1": "2002",
                            "o2": "2003",
                            "o3": "2004",
                            "o4": "2005"
                        }],
                        "user_answer": [2, 3, 3, 4],
                        "correct_answer": [3, 3, 3, 4],
                        "prize": [
                        {
                            "id": 1,
                            "name": "手机支架",
                            "image": "https://dummyimage.com/400x300",
                            "level": 2,
                            "amount": 20,
                            "remain": 20,
                            "project_id": 1
                        },
                        {
                            "id": 2,
                            "name": "山大信纸",
                            "image": "https://dummyimage.com/400x300",
                            "level": 1,
                            "amount": 10,
                            "remain": 10,
                            "project_id": 1
                        }],
                        "raffle_times": 5,
                        "raffle_result": [3, 3, 3, 1],
                        "raffle_remain_times": 1,
                        "raffle_time": "2025-03-01T00:00:00"
                }
            }
        }
    
    
class ProjectWithQuestionsAndPrizesForManager(ProjectPublic):
    question: list[QuestionPublicWithAnswer] = []
    prize: list[PrizePublic] = []
    
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
                            "o1": "1899",
                            "o2": "1900",
                            "o3": "1901",
                            "o4": "1902",
                            "a": 3
                        },
                        {
                            "id": 2,
                            "q": "兴隆山校区在哪一年建成？",
                            "o1": "2002",
                            "o2": "2003",
                            "o3": "2004",
                            "o4": "2005",
                            "a": 3
                        }],
                        "prize": [
                        {
                            "id": 1,
                            "name": "手机支架",
                            "image": "https://dummyimage.com/400x300",
                            "level": 2,
                            "amount": 20,
                            "remain": 20,
                            "project_id": 1
                        },
                        {
                            "id": 2,
                            "name": "山大信纸",
                            "image": "https://dummyimage.com/400x300",
                            "level": 1,
                            "amount": 10,
                            "remain": 10,
                            "project_id": 1
                        }]
                }
            }
        }
    
    
class ProjectWithQuestionsAndPrizesEmpty(ProjectPublic):
    question: list[QuestionPublicWithAnswer] = []
    prize: list[PrizePublic] = []
    
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
                        "question": [],
                        "prize": []
                }
            }
        }
    

class AnswerQuestions(BaseModel):
    project_id: int
    answer: list[int]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": 1,
                "answer": [2, 3, 3, 4]
            }
        }
    }

