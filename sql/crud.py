import schemas as sch
import sql.models as models
from sql.database import get_session
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status
from routers.login import verify_token
from fastapi import Query, Path
import datetime, random


MAX_RAFFLE_TIMES = 5


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
    records = session.exec(select(models.Record).filter_by(project_id=project_id)).all()
    project_data = sch.ProjectWithQuestionsAndPrizesForManager.model_validate(project)
    if records != []:
        for record in records:
            if record.answer_time and record.answer:
                user = session.get(models.User, record.user_id)
                qa_participant = sch.QA_ParticipantPublic(id=user.id,
                                                        username=user.username,
                                                        answer=eval(record.answer),
                                                        answer_time=record.answer_time)
                project_data.qa_participant.append(qa_participant)
            if record.raffle_time and record.raffle_result:
                user = session.get(models.User, record.user_id)
                raffle_participant = sch.RaffleParticipantPublic(id=user.id, 
                                                                username=user.username,
                                                                raffle_result=eval(record.raffle_result),
                                                                raffle_time=record.raffle_time,
                                                                prize_claim_status=record.prize_claim_status)
                project_data.raffle_participant.append(raffle_participant)
        return project_data
    return project


def read_project_details_by_user(project_id: int, 
                                user = Depends(verify_token),
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
    record = session.exec(select(models.Record).filter_by(user_id=user.id, project_id=project_id)).first()
    questions = session.exec(select(models.Question).filter_by(project_id=project_id)).all()
    prizes = session.exec(select(models.Prize).filter_by(project_id=project_id)).all()
    if record:
        project_data = sch.ProjectWithQuestionsAndPrizesForUser.model_validate(project)
        project_data.raffle_time = record.raffle_time
        if questions != [] and prizes != []:  # 如果是问答+抽奖项目，有记录说明至少已经答了题
            project_data.user_answer = eval(record.answer)
            project_data.correct_answer = [question.a for question in questions]
            project_data.raffle_times = record.raffle_times
            if record.raffle_result:
                project_data.raffle_result = eval(record.raffle_result)
            else:
                project_data.raffle_result = []
            project_data.raffle_remain_times = MAX_RAFFLE_TIMES - len(project_data.raffle_result)
            return project_data
        elif questions != [] and prizes == []:  # 如果是仅问答项目，有记录说明已经答了题
            project_data.user_answer = eval(record.answer)
            project_data.correct_answer = [question.a for question in questions]
            return project_data
        elif questions == [] and prizes != []:  # 如果是仅抽奖项目，有记录说明已经抽过奖
            project_data.raffle_times = 1
            project_data.raffle_result = eval(record.raffle_result)
            project_data.raffle_remain_times = 0
            return project_data
    else:
        if questions == [] and prizes != []: # 没记录并且是仅抽奖项目，说明还没参与抽奖
            project_data = sch.ProjectWithQuestionsAndPrizesForUser.model_validate(project)
            project_data.raffle_times = 1
            project_data.raffle_remain_times = 1
            return project_data
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
    
    
def delete_project(project_id: int, 
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    questions = session.exec(select(models.Question).filter_by(project_id=project_id)).all()
    for question in questions:
        session.delete(question)
    prizes = session.exec(select(models.Prize).filter_by(project_id=project_id)).all()
    for prize in prizes:
        session.delete(prize)
    session.delete(project)
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


def answer_question(user_answer: sch.AnswerQuestions,
                    user = Depends(verify_token),
                    session: Session=Depends(get_session)):
    questions = session.exec(select(models.Question).filter_by(project_id=user_answer.project_id)).all()
    correct_answer = [question.a for question in questions]
    question_num = len(questions)
    correct_num = 0
    for i in range(question_num):
        if user_answer.answer[i] == correct_answer[i]:
            correct_num += 1
    correct_rate = correct_num / question_num
    raffle_times = int(correct_rate * MAX_RAFFLE_TIMES + 0.5)   # 四舍五入，注意用round()函数会出现银行家舍入问题
    record_in_db = session.exec(select(models.Record).filter_by(user_id=user.id, 
                                project_id=user_answer.project_id)).first()
    if not record_in_db:
        record = models.Record(user_id=user.id,
                            project_id=user_answer.project_id,
                            answer=str(user_answer.answer),
                            answer_time=datetime.datetime.now(),
                            raffle_times=raffle_times)
        session.add(record)
        session.commit()
        session.refresh(record)
    project = read_project_details_by_user(project_id=user_answer.project_id, user=user, session=session)
    return project


def raffle_prize(project_id: int,
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Project not found.")
    if project.status == 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Project has ended.")
    record = session.exec(select(models.Record).filter_by(user_id=user.id, project_id=project_id)).first()
    if record and record.raffle_result:
        already_raffled_prize = eval(record.raffle_result)
    else:
        already_raffled_prize = []
    prizes = session.exec(select(models.Prize).filter_by(project_id=project_id)).all()
    prize_pool = {}
    for prize in prizes:
        if prize.remain > 0:
            if prize.id not in already_raffled_prize:   # 如果这个奖品还没抽到过，就加入奖池
                prize_pool[prize.id] = prize.remain
            else:
                # 如果这个奖品已经被抽到过，如果是正常奖品，就不加入奖池。如果是安慰奖，还是加入奖池。
                if prize.level == 0:    
                    prize_pool[prize.id] = prize.remain
    if not record:      # 没有记录就能抽奖说明是仅抽奖项目
        result = random.choices(list(prize_pool.keys()), weights=list(prize_pool.values()), k=1)
        record_create = models.Record(user_id=user.id, project_id=project_id, 
                                    raffle_result=str(result), 
                                    raffle_time=datetime.datetime.now())
        session.add(record_create)
        session.commit()
        session.refresh(record_create)
        prize_get = session.get(models.Prize, result[0])
        prize_get.remain -= 1
        session.add(prize_get)
        session.commit()
        session.refresh(prize_get)
    else:
        result = random.choices(list(prize_pool.keys()), weights=list(prize_pool.values()), k=1)
        if not record.raffle_result:
            record.raffle_result = str(result)
            record.raffle_time = datetime.datetime.now()
            prize_get = session.get(models.Prize, result[0])
            prize_get.remain -= 1
            session.add(prize_get)
            session.commit()
            session.refresh(prize_get)
        elif record.raffle_times > len(eval(record.raffle_result)):
            record.raffle_result = str(eval(record.raffle_result) + result)
            record.raffle_time = datetime.datetime.now()
            session.add(record)
            session.commit()
            session.refresh(record)
            prize_get = session.get(models.Prize, result[0])
            prize_get.remain -= 1
            session.add(prize_get)
            session.commit()
            session.refresh(prize_get)
    project = read_project_details_by_user(project_id=project_id, user=user, session=session)
    return project


def read_records_by_user(user = Depends(verify_token),
                        page: int = Query(default=1, ge=1, description="展示第几页（从1开始）"),
                        page_size: int = Query(default=10, ge=1, description="每一页展示的项目数"),
                        session: Session=Depends(get_session)):
    records = session.exec(select(models.Record).filter_by(user_id=user.id)).all()
    projects = []
    for record in records:
        project = session.get(models.Project, record.project_id)
        projects.append(project)
    return projects[(page-1)*page_size:page*page_size]


def claim_prize(project_id: int = Path(description="兑奖项目的id"), 
                user_id: int = Path(description="兑奖用户的id"), 
                user = Depends(verify_token),
                session: Session=Depends(get_session)):
    check_permission(user)
    record = session.exec(select(models.Record).filter_by(user_id=user_id, project_id=project_id)).first()
    if not record or not record.raffle_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Record not found.")
    record.prize_claim_status = True
    session.add(record)
    session.commit()
    session.refresh(record)
    project = read_project_details(project_id=project_id, user=user, session=session)
    return project