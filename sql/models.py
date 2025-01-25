from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    hashed_password: str
    campus: str | None = Field(default=None)
    department: str | None = Field(default=None)
    qq: str | None = Field(default=None)
    wx: str | None = Field(default=None)
    project: list["Project"] = Relationship(back_populates="creater", cascade_delete=True)
    

class Project(SQLModel, table=True):
    uuid: str = Field(primary_key=True)
    name: str
    description: str | None = Field(default=None)
    start_time: datetime
    dead_line: datetime
    status: int = Field(default=0)
    project_type: int
    browse_times: int = Field(default=0)
    qa_participant_num: int = Field(default=0)
    raffle_participant_num: int = Field(default=0)
    prize_claim_way: int | None = Field(default=None)
    correct_item_num: int | None = Field(default=None)
    total_raffle_times: int | None = Field(default=None)
    prize_claim_place: str | None = Field(default=None)
    prize_claim_time: str | None = Field(default=None)
    qr_code: str | None = Field(default=None)
    creater_id: int | None = Field(default=None, foreign_key="user.id", ondelete="CASCADE")
    creater: User = Relationship(back_populates="project")
    question: list["Question"] = Relationship(back_populates="project", cascade_delete=True)
    prize: list["Prize"] = Relationship(back_populates="project",  cascade_delete=True)
    record: list["Record"] = Relationship(back_populates="project", cascade_delete=True)
    
    
class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    q: str
    o1: str
    o2: str
    o3: str
    o4: str
    a: int
    project_uuid: str = Field(foreign_key="project.uuid", ondelete="CASCADE")
    project: Project = Relationship(back_populates="question")
    
    
class Prize(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    image: str | None = Field(default=None)
    level: int
    amount: int
    remain: int
    project_uuid: str = Field(foreign_key="project.uuid", ondelete="CASCADE")
    project: Project= Relationship(back_populates="prize")
    
    
class Record(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    participant_uuid: str
    project_uuid: str = Field(foreign_key="project.uuid", ondelete="CASCADE")
    project: Project = Relationship(back_populates="record")
    record_type: int    # 1：答题记录 2：抽奖记录
    correct_rate: float | None = Field(default=None)
    
    