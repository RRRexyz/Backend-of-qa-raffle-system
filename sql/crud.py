import schemas as sch
import sql.models as models
from sql.database import get_session
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status
from routers.login import verify_token



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


def read_projects_by_manager(user = Depends(verify_token),
                            session: Session=Depends(get_session)):
    check_permission(user)
    projects = session.exec(select(models.Project).filter_by(creater_id=user.id)).all()
    return projects


def read_project_details(project_id: int, session: Session=Depends(get_session)):
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    return project


def add_question(question_create: sch.QuestionCreate,
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    question = models.Question.model_validate(question_create)
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


