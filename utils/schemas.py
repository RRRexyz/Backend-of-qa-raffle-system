from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from utils.globalvar import WEBSITE_URL, SERVER_URL


class UserRegister(BaseModel):
    username: str = Field(description="用户名，全局唯一")
    password: str = Field(description="密码")
    campus: str | None = Field(default=None, description="校区")
    department: str | None = Field(default=None, description="部门")
    qq: str | None = Field(default=None, description="QQ号")
    wx: str | None = Field(default=None, description="微信号")
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "admin",
                "password": "admin",
                "campus": "兴隆山校区",
                "department": "Web开发部",
                "qq": "2348747674",
                "wx": "afwr4646"
            }
        }
    }


class UserResponse(BaseModel):
    id: int | None
    username: str
    campus: str | None
    department: str | None
    qq: str | None
    wx: str | None
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "admin",
                "campus": "兴隆山校区",
                "department": "Web开发部",
                "qq": "2348747674",
                "wx": "afwr4646"
            }
        }
    }


class QuestionCreate(BaseModel):
    q: str
    o1: str
    o2: str
    o3: str
    o4: str
    a: int


class PrizeCreate(BaseModel):
    name: str
    image: str | None = Field(default=None)
    level: int
    amount: int


class ProjectCreate(BaseModel):
    name: str
    description: str | None = Field(default=None)
    start_time: datetime
    dead_line: datetime
    question: list[QuestionCreate] = Field(default_factory=list)
    prize: list[PrizeCreate] = Field(default_factory=list)
    prize_claim_way: int | None = Field(default=None)
    correct_item_num: int | None = Field(default=None)
    total_raffle_times: int | None = Field(default=None)
    prize_claim_place: str | None = Field(default=None)
    prize_claim_time: str | None = Field(default=None)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "毕业跑", 
                "description": "毕业跑活动展台",
                "start_time": "2025-02-01 10:00:00",
                "dead_line": "2025-03-15 10:00:00",
                "question": [
                    {
                        "q": "山东大学是什么时候成立的？",
                        "o1": "1900",
                        "o2": "1901",
                        "o3": "1902",
                        "o4": "1903",
                        "a": 2
                    }
                ],
                "prize": [
                    {
                        "name": "手机支架",
                        "level": 1,
                        "image": "https://dummyimage.com/400x300",
                        "amount": 100
                    }
                ],
                "prize_claim_way": 1,
                "correct_item_num": 5,
                "total_raffle_times": 1,
                "prize_claim_place": "展台",
                "prize_claim_time": "2025-03-16 10:00:00"
            }
        }
    }


class ProjectCreateResponse(BaseModel):
    project_uuid: UUID = Field(description="项目UUID")


class QuestionResponse(QuestionCreate):
    id: int | None


class PrizeResponse(PrizeCreate):
    id: int | None
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "手机支架",
                "level": 1,
                "image": "https://dummyimage.com/400x300",
                "amount": 100
            }
        }
    }
    
    
class ProjectResponseForAdmin(PrizeCreate):
    id: int | None
    remain: int = Field(description="奖品剩余数量")
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "手机支架",
                "level": 1,
                "image": "https://dummyimage.com/400x300",
                "amount": 100,
                "remain": 100
            }
        }
    }
    

class ProjectDetailResponse(ProjectCreate):
    uuid: UUID = Field(description="项目UUID")
    status: int = Field(description="项目状态，0表示未开始，1表示进行中，2表示已结束")
    project_type: int = Field(
        description="项目类型，0表示空项目，1表示仅抽奖项目，2表示仅问答项目，3表示问答抽奖项目，-1表示未知类型")
    browse_times: int = Field(description="浏览次数")
    qa_participant_num: int = Field(description="问答参与人数")
    raffle_participant_num: int = Field(description="抽奖参与人数")
    question: list[QuestionResponse] = Field(description="问答列表带答案")
    prize: list[ProjectResponseForAdmin] = Field(description="奖品列表带剩余数量")

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "name": "毕业跑", 
                "description": "毕业跑活动展台",
                "start_time": "2025-02-01T10:00:00",
                "dead_line": "2025-03-15T10:00:00",
                "question": [
                    {
                        "id": 1,
                        "q": "山东大学是什么时候成立的？",
                        "o1": "1900",
                        "o2": "1901",
                        "o3": "1902",
                        "o4": "1903",
                        "a": 2
                    }
                ],
                "prize": [
                    {
                        "id": 1,
                        "name": "手机支架",
                        "level": 1,
                        "image": "https://dummyimage.com/400x300",
                        "amount": 100,
                        "remain": 100
                    }
                ],
                "prize_claim_way": 1,
                "correct_item_num": 5,
                "total_raffle_times": 1,
                "prize_claim_place": "展台",
                "prize_claim_time": "下周五晚7-9点",
                "status": 1,
                "project_type": 3,
                "browse_times": 100,
                "qa_participant_num": 10,
                "raffle_participant_num": 10
            }
        }
    }
    
    
class ProjectQRCodeResponse(BaseModel):
    qr_code_url: str = Field(description="项目二维码URL，其中包含的内容就是project_participate_url")
    project_participate_url: str = Field(description="项目参与链接")
    model_config = {
        "json_schema_extra": {
            "example": {
                "qr_code_url": "https://dummyimage.com/400x300",
                "project_participate_url": f"{WEBSITE_URL}/project/1820380e-22d0-4f68-97ed-bd49f563100b"
            }
        }
    }
    

class AnswerSubmit(BaseModel):
    project_uuid: str = Field(description="项目UUID")
    user_answer: list[int] = Field(description="用户答案")
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "user_answer": [2, 1, 4, 3, 2]
            }
        }
    }
    
    
class AnswerSubmitResponse(BaseModel):
    project_uuid: UUID = Field(description="项目UUID")
    user_uuid: UUID = Field(description="用户UUID")
    user_answer: list[int] = Field(description="用户提交的答案数组")
    correct_answer: list[int] = Field(description="正确答案数组")
    user_correct_num: int = Field(description="用户答对的题目数量")
    total_item_num: int = Field(description="题目总量")
    correct_rate: float = Field(description="用户正确率")
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "user_uuid": "2fcfa550-d93b-11ef-a2a9-832c32728689",
                "user_answer": [2, 1, 4, 3, 2],
                "correct_answer": [2, 1, 3, 3, 2],
                "user_correct_num": 4,
                "total_item_num": 5,
                "correct_rate": 0.8
            }
        }
    }
    
        
class RaffleResult(BaseModel):
    project_uuid: str = Field(description="项目UUID")
    user_uuid: str | None = Field(default=None, description="用户UUID")
    prize_raffled: list[int] = Field(default_factory=list, description="用户抽到的所有奖品的id数组")
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "user_uuid": "2fcfa550-d93b-11ef-a2a9-832c32728689",
                "prize_raffled": [1, 2, 3]
            }
        }
    }
    
    
class ClaimPrizeQRCodeResponse(BaseModel):
    project_uuid: UUID = Field(description="项目UUID")
    user_uuid: UUID = Field(description="用户UUID")
    qr_code_url: str = Field(description="用户兑奖二维码URL，其中包含的内容就是claim_prize_url")
    claim_prize_url: str = Field(description="用户兑奖链接")
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "user_uuid": "2fcfa550-d93b-11ef-a2a9-832c32728689",
                "qr_code_url": "https://dummyimage.com/400x300",
                "claim_prize_url": f"{WEBSITE_URL}/claim-prize?project_uuid=1820380e-22d0-4f68-97ed-bd49f563100b&user_uuid=2fcfa550-d93b-11ef-a2a9-832c32728689&prize_raffled=1&prize_raffled=2&prize_raffled=3"
            }
        }
    }
    
    
class PrizeInfo(BaseModel):
    id: int | None
    name: str
    level: int
    image: str | None = Field(default=None)


    
class ClaimPrizeInfo(BaseModel):
    claim_prize_status: bool = Field(description="是否已兑奖，True表示已兑奖，False表示未兑奖")
    prizes: list[PrizeInfo] = Field(default_factory=list, description="中奖奖品列表")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "claim_prize_status": False,
                "prizes": [
                    {
                        "id": 1,
                        "name": "手机支架",
                        "level": 1,
                        "image": "https://dummyimage.com/400x300",
                    }
                ]
            }
        }
    }   
    
    
class ClaimPrizeSubmit(BaseModel):
    project_uuid: str = Field(description="项目UUID")
    user_uuid: str = Field(description="用户UUID")
    model_config = {    
        "json_schema_extra": {
            "example": {
                "project_uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "user_uuid": "2fcfa550-d93b-11ef-a2a9-832c32728689"
            }
        }
    }


class QuestionPublic(BaseModel):
    id: int | None
    q: str
    o1: str
    o2: str
    o3: str
    o4: str

    
class PrizePublic(BaseModel):
    id: int | None
    name: str
    level: int
    image: str | None = Field(default=None)
    amount: int
    
    
class ProjectWithQuestion(BaseModel):
    uuid: UUID = Field(description="项目UUID")
    name: str = Field(description="项目名称")
    description: str | None = Field(default=None, description="项目描述")
    start_time: datetime = Field(description="项目开始时间")
    dead_line: datetime = Field(description="项目截止时间")
    status: int = Field(description="项目状态，0表示未开始，1表示进行中，2表示已结束")
    project_type: int = Field(
        description="项目类型，0表示空项目，1表示仅抽奖项目，2表示仅问答项目，3表示问答抽奖项目，-1表示未知类型")
    question: list[QuestionPublic] = Field(default_factory=list, description="问答列表")
    browse_times: int = Field(description="项目浏览次数")
    qa_participant_num: int = Field(description="问答参与人数")
    raffle_participant_num: int = Field(description="抽奖参与人数")
    prize_claim_way: int | None = Field(description="奖品兑奖方式，0表示展台现场兑奖，1表示指定地点兑奖")
    correct_item_num: int | None = Field(description="问答抽奖项目中获得抽奖机会需要答对的题目数量")
    total_raffle_times: int | None = Field(description="总共可抽奖次数")
    prize_claim_place: str | None = Field(description="指定地点兑奖项目的兑奖地点")
    prize_claim_time: str | None = Field(description="指定地点兑奖项目的兑奖时间")
    creater_id: int = Field(description="项目创建者的id")
    creater: UserResponse = Field(description="项目创建者的信息")
    model_config = {
        "json_schema_extra": {
            "example": {                
                "uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "name": "毕业跑", 
                "description": "毕业跑活动展台",
                "start_time": "2025-02-01T10:00:00",
                "dead_line": "2025-03-15T10:00:00",
                "status": 1,
                "project_type": 3,
                "question": [
                    {
                        "id": 1,
                        "q": "山东大学是什么时候成立的？",
                        "o1": "1900",
                        "o2": "1901",
                        "o3": "1902",
                        "o4": "1903"
                    }
                ],
                "browse_times": 100,
                "qa_participant_num": 10,
                "raffle_participant_num": 100,
                "prize_claim_way": 1,
                "correct_item_num": 5,
                "total_raffle_times": 1,
                "prize_claim_place": "展台",
                "prize_claim_time": "2025-03-16T10:00:00",
                "creater_id": 1,
                "creater": {
                "username": "admin",
                "password": "admin",
                "campus": "兴隆山校区",
                "department": "Web开发部",
                "qq": "2348747674",
                "wx": "afwr4646"
            }
            }
        }
    }
    
    
class ProjectWithPrize(BaseModel):
    uuid: UUID = Field(description="项目UUID")
    name: str = Field(description="项目名称")
    description: str | None = Field(default=None, description="项目描述")
    start_time: datetime = Field(description="项目开始时间")
    dead_line: datetime = Field(description="项目截止时间")
    status: int = Field(description="项目状态，0表示未开始，1表示进行中，2表示已结束")
    project_type: int = Field(
        description="项目类型，0表示空项目，1表示仅抽奖项目，2表示仅问答项目，3表示问答抽奖项目，-1表示未知类型")
    prize: list[PrizePublic] = Field(default_factory=list, description="抽奖列表")
    browse_times: int = Field(description="项目浏览次数")
    qa_participant_num: int = Field(description="问答参与人数")
    raffle_participant_num: int = Field(description="抽奖参与人数")
    prize_claim_way: int | None = Field(description="奖品兑奖方式，0表示展台现场兑奖，1表示指定地点兑奖")
    correct_item_num: int | None = Field(description="问答抽奖项目中获得抽奖机会需要答对的题目数量")
    total_raffle_times: int | None = Field(description="总共可抽奖次数")
    prize_claim_place: str | None = Field(description="指定地点兑奖项目的兑奖地点")
    prize_claim_time: str | None = Field(description="指定地点兑奖项目的兑奖时间")
    creater_id: int = Field(description="项目创建者的id")
    creater: UserResponse = Field(description="项目创建者的信息")
    model_config = {
        "json_schema_extra": {
            "example": {                
                "uuid": "1820380e-22d0-4f68-97ed-bd49f563100b",
                "name": "毕业跑", 
                "description": "毕业跑活动展台",
                "start_time": "2025-02-01T10:00:00",
                "dead_line": "2025-03-15T10:00:00",
                "status": 1,
                "project_type": 3,
                "prize": [
                    {
                        "id": 1,
                        "name": "手机支架",
                        "level": 1,
                        "image": "https://dummyimage.com/400x300",
                        "amount": 100
                    }
                ],
                "browse_times": 100,
                "qa_participant_num": 10,
                "raffle_participant_num": 100,
                "prize_claim_way": 1,
                "correct_item_num": 5,
                "total_raffle_times": 1,
                "prize_claim_place": "展台",
                "prize_claim_time": "2025-03-16T10:00:00",
                "creater_id": 1,
                "creater": {
                    "username": "admin",
                    "password": "admin",
                    "campus": "兴隆山校区",
                    "department": "Web开发部",
                    "qq": "2348747674",
                    "wx": "afwr4646"
            }
            }
        }
    }
    
    
class MyProjectPreview(BaseModel):
    uuid: UUID = Field(description="项目UUID")
    name: str = Field(description="项目名称")
    description: str | None = Field(default=None, description="项目描述")
    start_time: datetime = Field(description="项目开始时间")
    dead_line: datetime = Field(description="项目截止时间")
    status: int = Field(description="项目状态，0表示未开始，1表示进行中，2表示已结束")
    project_type: int = Field(
        description="项目类型，0表示空项目，1表示仅抽奖项目，2表示仅问答项目，3表示问答抽奖项目，-1表示未知类型")
    browse_times: int = Field(description="项目浏览次数")
    qa_participant_num: int = Field(description="问答参与人数")
    raffle_participant_num: int = Field(description="抽奖参与人数")
    qa_average_correct_rate: float = Field(description="问答平均正确率")
    model_config = {    
        "json_schema_extra": {
            "example": [
                {
                    "uuid": "8c1bfc71-da68-11ef-bcfd-38fc98613d7e",
                    "name": "毕业跑",
                    "description": "毕业跑展台活动",
                    "start_time": "2025-02-01T10:00:00",
                    "dead_line": "2025-03-15T14:00:00",
                    "status": 0,
                    "project_type": 3,
                    "browse_times": 5,
                    "qa_participant_num": 2,
                    "raffle_participant_num": 5,
                    "qa_average_correct_rate": 0.8333333333333333
                }
            ]
        }
    }
    
    
class AllProjectPreview(BaseModel):
    uuid: UUID = Field(description="项目UUID")
    name: str = Field(description="项目名称")
    description: str | None = Field(default=None, description="项目描述")
    start_time: datetime = Field(description="项目开始时间")
    dead_line: datetime = Field(description="项目截止时间")
    status: int = Field(description="项目状态，0表示未开始，1表示进行中，2表示已结束")
    project_type: int = Field(
        description="项目类型，0表示空项目，1表示仅抽奖项目，2表示仅问答项目，3表示问答抽奖项目，-1表示未知类型")
    browse_times: int = Field(description="项目浏览次数")
    qa_participant_num: int = Field(description="问答参与人数")
    raffle_participant_num: int = Field(description="抽奖参与人数")
    qa_average_correct_rate: float = Field(description="问答平均正确率")
    creater_id: int = Field(description="项目创建者的id")
    creater: UserResponse = Field(description="项目创建者的信息")
    model_config = {    
        "json_schema_extra": {
            "example": [
                {
                    "uuid": "8c1bfc71-da68-11ef-bcfd-38fc98613d7e",
                    "name": "毕业跑",
                    "description": "毕业跑展台活动",
                    "start_time": "2025-02-01T10:00:00",
                    "dead_line": "2025-03-15T14:00:00",
                    "status": 0,
                    "project_type": 3,
                    "browse_times": 5,
                    "qa_participant_num": 2,
                    "raffle_participant_num": 5,
                    "qa_average_correct_rate": 0.8333333333333333,
                    "creater_id": 1,
                    "creater": {
                        "username": "admin",
                        "password": "admin",
                        "campus": "兴隆山校区",
                        "department": "Web开发部",
                        "qq": "2348747674",
                        "wx": "afwr4646"
                    }
                }
            ]
        }
    }