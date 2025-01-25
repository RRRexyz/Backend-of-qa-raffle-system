from sqlmodel import create_engine, SQLModel, Session, text
from typing import Annotated
from fastapi import Depends
import sql.models # 这是为了导入定义的数据库表，否则创建数据库时这些表不会被创建


sqlite_file_name = "qa_raffle.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    with engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))  # for SQLite only
    

def get_session():
    with Session(engine) as session:
        yield session   


SessionDep = Annotated[Session, Depends(get_session)]
