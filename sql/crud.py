import schemas as sch
import sql.models as models
from sql.database import get_session
from sqlmodel import Session
from fastapi import Depends, HTTPException, status
from routers.login import verify_token



def permission_check(user: models.User):
    if user.manage_permission == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="No permission.")
        

def create_project(project_create: sch.ProjectCreate, 
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    permission_check(user)
    project = models.Project.model_validate(project_create)
    project.creater_id = user.id
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def read_projects_by_manager():
    pass


def add_question(question_create: sch.QuestionCreate,
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    permission_check(user)
    question = models.Question.model_validate(question_create)
    pass