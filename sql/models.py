from sqlmodel import SQLModel, Field, Relationship
import datetime



class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    hashed_password: str
    qq: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    manage_permission: bool = Field(default=False)
    
    project: list["Project"] = Relationship(back_populates="creater")
    record: list["Record"] = Relationship(back_populates="user")
    

class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = Field(default=None)
    create_time: datetime.datetime = Field(default=datetime.datetime.now())
    deadline: datetime.datetime
    status: int = Field(default=0)
    browse_times: int = Field(default=0)

    creater_id: int | None = Field(default=None, foreign_key="user.id")
    
    creater: User | None = Relationship(back_populates="project")
    
    question: list["Question"] = Relationship(back_populates="project")
    prize: list["Prize"] = Relationship(back_populates="project")
    participant: list["Record"] = Relationship(back_populates="project")
    
    
class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    q: str
    a: int
    
    project_id: int | None = Field(default=None, foreign_key="project.id")
    
    project: Project | None = Relationship(back_populates="question")


class Prize(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default=None)
    image: str | None = Field(default=None)
    level: int = Field(default=0)
    amount: int = Field(default=0)
    probability: float = Field(default=0.0)
    
    project_id: int | None = Field(default=None, foreign_key="project.id")
    
    project: Project | None = Relationship(back_populates="prize")
    
    
class Record(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    project_id: int | None = Field(default=None, foreign_key="project.id")
    answer: str = Field(default=None, nullable=True)
    answer_time: datetime.datetime = Field(default=datetime.datetime.now())
    raffle_times: int = Field(default=0)
    raffle_result: int | None = Field(default=None)
    raffle_time: datetime.datetime = Field(default=datetime.datetime.now())
    prize_claim_status: bool = Field(default=False)
    
    user : User | None = Relationship(back_populates="record")
    project: Project | None = Relationship(back_populates="participant")

