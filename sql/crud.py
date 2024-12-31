import schemas as sch
import sql.models as models
from sql.database import get_session
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status
from routers.login import verify_token
from fastapi import Query
import datetime



def check_project_timeout(project) -> bool:
    nowtime = datetime.datetime.now()
    if project.deadline <= nowtime and project.status == 1:
        project.status = 2
        return True
    elif project.deadline > nowtime and project.status == 2:
        project.status = 1
        return True
    return False


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
    check_project_timeout(project)
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
    
    for project in projects:
        if check_project_timeout(project):
            session.add(project)
            session.commit()
            session.refresh(project)
    return projects


def read_project_details(project_id: int, 
                        user = Depends(verify_token),
                        session: Session=Depends(get_session)):
    check_permission(user)
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
        
    if check_project_timeout(project):
        session.add(project)
        session.commit()
        session.refresh(project)
    return project


def read_project_details_by_user(project_id: int, 
                                session: Session=Depends(get_session)):
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    if project.status == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Project not published.")
    project.browse_times += 1
    check_project_timeout(project)
    session.add(project)
    session.commit()
    session.refresh(project)
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


def update_question(question_id: int, question_update: sch.QuestionUpdate,
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    question = session.get(models.Question, question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Question not found.")
    question_data = question_update.model_dump(exclude_unset=True)
    question.sqlmodel_update(question_data)
    session.add(question)
    session.commit()
    session.refresh(question)
    return question
    

def delete_question(question_id: int,
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    question = session.get(models.Question, question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Question not found.")
    session.delete(question)
    session.commit()
    

def add_prize(prize_add: sch.PrizeAdd,
            user = Depends(verify_token),
            session: Session=Depends(get_session)):
    check_permission(user)
    prize_add_dict = prize_add.model_dump()
    prize_add_dict['remain'] = prize_add.amount
    prize = models.Prize(**prize_add_dict)
    # prize = models.Prize.model_validate(prize_add_new)
    session.add(prize)
    session.commit()
    session.refresh(prize)
    return prize


def update_prize(prize_id: int, prize_update: sch.PrizeUpdate,
            user = Depends(verify_token),
            session: Session=Depends(get_session)):
    check_permission(user)
    prize = session.get(models.Prize, prize_id)
    if not prize:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Prize not found.")
    prize_data = prize_update.model_dump(exclude_unset=True)
    if 'amount' in prize_data:
        amount_change = prize_data['amount'] - prize.amount
        prize_data["remain"] = prize.remain + amount_change
        if prize_data["remain"] < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Prize amount is less than already raffled.")
    prize.sqlmodel_update(prize_data)
    session.add(prize)
    session.commit()
    session.refresh(prize)
    return prize


def delete_prize(prize_id: int,
            user = Depends(verify_token),
            session: Session=Depends(get_session)):
    check_permission(user)
    prize = session.get(models.Prize, prize_id)
    if not prize:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Prize not found.")
    session.delete(prize)
    session.commit()
    
    
def publish_project(project_id: int,
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    if project.status == 0:
        project.status = 1
        session.add(project)
        session.commit()
        session.refresh(project)
    return project


