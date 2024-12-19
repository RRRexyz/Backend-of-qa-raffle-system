import schemas as sch
import sql.models as models
from sql.database import get_session
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status
from routers.login import verify_token
from fastapi import Query



def check_permission(user: models.User):
    if user.manage_permission == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="No permission.")
        

def create_project(project_create: sch.ProjectCreate, 
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    project = models.Project.model_validate(project_create)
    project.creater_id = user.id
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def update_project(project_id: int, project_update: sch.ProjectUpdate, 
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    project_data = project_update.model_dump(exclude_unset=True)
    project.sqlmodel_update(project_data)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def delete_project(project_id: int, 
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    session.delete(project)
    session.commit()


def read_projects_by_manager(user = Depends(verify_token),
                            page: int = Query(default=1, ge=1, description="展示第几页（从1开始）"),
                            page_size: int = Query(default=10, ge=1, description="每一页展示的项目数"),
                            session: Session=Depends(get_session)):
    check_permission(user)
    projects = session.exec(select(models.Project).offset((page-1)*page_size).limit(page_size)
                            .filter_by(creater_id=user.id)).all()
    return projects


def read_project_details(project_id: int, session: Session=Depends(get_session)):
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    return project


def add_question(question_add: sch.QuestionAdd,
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    question = models.Question.model_validate(question_add)
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


def add_prize(prize_add: sch.PrizeAdd,
            user = Depends(verify_token),
            session: Session=Depends(get_session)):
    check_permission(user)
    prize = models.Prize.model_validate(prize_add)
    session.add(prize)
    session.commit()
    session.refresh(prize)
    return prize
