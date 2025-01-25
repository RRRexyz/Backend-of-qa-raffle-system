from fastapi import APIRouter, Query, Path, Depends, HTTPException, status
import utils.schemas as schemas 
from sqlmodel import Session, select
from sql.database import get_session
import sql.models as models
from uuid import uuid1
import random
from utils.qrcode import generate_qrcode
from utils.globalvar import WEBSITE_URL, SERVER_URL
from datetime import datetime


router = APIRouter()


@router.get("/project/{project_uuid}/answer", 
            response_model=schemas.ProjectWithQuestion,
            response_description="返回项目的基本信息和问答题目",
            responses={404: {"description": "项目不存在"}},
            summary="获取项目的问答题目")
async def read_project_quetsion_details(project_uuid: str = Path(description="项目uuid"),
                                        session: Session = Depends(get_session)):
    """用户扫描项目二维码进入项目界面时，先调用此接口获取项目的基本信息和问答题目，用于展示。
    """
    project = session.get(models.Project, project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    # 检查项目状态
    now_time = datetime.now()
    start_time = project.start_time
    dead_line = project.dead_line
    if project.status == 0:
        if start_time < now_time < dead_line:
            project.status = 1 # 项目开始，状态改为进行中
        elif now_time > dead_line:
            project.status = 2 # 项目已结束，状态改为已结束
    elif project.status == 1:
        if now_time < start_time:
            project.status = 0 # 项目未开始，状态改为未开始
        elif now_time > dead_line:
            project.status = 2 # 项目已结束，状态改为已结束
    elif project.status == 2:
        if now_time < start_time:
            project.status = 0 # 项目未开始，状态改为未开始
        elif start_time < now_time < dead_line:
            project.status = 1 # 项目开始，状态改为进行中
    # 项目浏览次数加一
    project.browse_times += 1
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/project/{project_uuid}/raffle",
            response_model=schemas.ProjectWithPrize,
            response_description="返回项目的基本信息和抽奖信息",
            responses={404: {"description": "项目不存在"}},
            summary="获取项目的抽奖信息")
async def read_project_raffle_details(project_uuid: str = Path(description="项目uuid"),
                                    session: Session = Depends(get_session)):
    """在抽奖界面调用此接口获取项目的基本信息和抽奖信息，用于展示。
    """
    project = session.get(models.Project, project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    return project


@router.post("/answer", response_model=schemas.AnswerSubmitResponse,
            response_description="返回用户作答结果信息",
            responses={404: {"description": "项目不存在"}},
            summary="提交答案")
async def submit_answer(answer_submit: schemas.AnswerSubmit,
                        session: Session = Depends(get_session)):
    """调用此接口需要保证：
    1. 项目状态为进行中(`status=1`)
    2. 用户答案数组长度与项目中题目数量一致
    3. 用户本地无答题记录
    
    调用后返回用户作答结果，用户答题情况不存入数据库，前端需要在本地存储，用于展示用户答题情况。
    """
    project = session.get(models.Project, answer_submit.project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    questions = session.exec(select(models.Question).filter_by(project_uuid=answer_submit.project_uuid)).all()
    correct_answer = [question.a for question in questions]
    question_num = len(questions)
    correct_num = 0
    for i in range(question_num):
        if answer_submit.user_answer[i] == correct_answer[i]:
            correct_num += 1
    correct_rate = correct_num / question_num
    user_uuid = str(uuid1())
    answer_record = models.Record(participant_uuid=user_uuid,
                                project_uuid=answer_submit.project_uuid,
                                record_type=1,  # 1表示答题记录
                                correct_rate=correct_rate)
    session.add(answer_record)
    session.commit()
    session.refresh(answer_record)
    # 项目问答的参与人数加一
    project.qa_participant_num += 1
    session.add(project)
    session.commit()
    session.refresh(project)
    response = schemas.AnswerSubmitResponse(project_uuid=answer_submit.project_uuid,
                                            user_uuid=user_uuid,
                                            user_answer=answer_submit.user_answer,
                                            correct_answer=correct_answer,
                                            user_correct_num=correct_num,
                                            total_item_num=question_num,
                                            correct_rate=correct_rate)
    return response


@router.post("/raffle/project/{project_uuid}",
            response_model= schemas.PrizeResponse,
            response_description="中奖奖品信息",
            responses={404: {"description": "项目不存在"},
                        400: {"description": "已无奖品可抽"}},
            summary="抽一次奖")
async def raffle_prize(project_uuid: str,
                session: Session = Depends(get_session)):
    """调用此接口需要保证：
    1. 项目状态为进行中(`status=1`)
    2. 用户剩余抽奖次数大于0
    3. 项目中存在奖品的剩余数量大于0
    
    调用后返回中奖信息，中奖信息不存入数据库，前端需要在本地存储，用于展示中奖结果。
    """
    project = session.get(models.Project, project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="项目不存在")
    prizes = session.exec(select(models.Prize).filter_by(project_uuid=project_uuid)).all()
    prize_pool = {} # 奖品池
    for prize in prizes:
        if prize.remain > 0:
            prize_pool[prize.id] = prize.remain
    if prize_pool == {}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="已无奖品可抽")
    # 从奖池中随机抽一个奖品
    result = random.choices(list(prize_pool.keys()), weights=list(prize_pool.values()), k=1)
    prize_raffled = session.get(models.Prize, result[0])
    # 奖品库存减一
    prize_raffled.remain -= 1
    session.add(prize_raffled)
    session.commit()
    session.refresh(prize_raffled)
    # 项目抽奖的参与人数加一
    project.raffle_participant_num += 1
    session.add(project)
    session.commit()
    session.refresh(project)
    return prize_raffled


@router.post("/qrcode/claim-prize", 
            response_model=schemas.ClaimPrizeQRCodeResponse,
            response_description="返回用户兑奖二维码信息",
            responses={404: {"description": "项目不存在"},
                        400: {"description": "奖品不能为空"}},
            summary="生成兑奖二维码")
async def generate_raffle_result_qrcode(raffle_result: schemas.RaffleResult,
                                        session: Session = Depends(get_session)):
    """调用此接口需要保证：
    1. 项目状态为进行中(`status=1`)
    2. 用户本地有中奖记录
    
    二维码中的内容为用户兑奖界面的网页url，形如：
    
    https://qarfl.rrrexyz.icu/claim-prize?project_uuid=1820380e-22d0-4f68-97ed-bd49f563100b&user_uuid=2fcfa550-d93b-11ef-a2a9-832c32728689&prize_raffled=1&prize_raffled=2&prize_raffled=3
    
    以查询参数的形式传递项目和用户uuid，以及中奖奖品的id数组。数组是以同名参数的形式传递的，多个奖品id以`&`分隔。
    
    此二维码url不存入数据库，前端需要在本地存储，用于展示用户兑奖二维码。
    """
    project = session.get(models.Project, raffle_result.project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    prize_raffled_query = ""
    for prize_id in raffle_result.prize_raffled:
        prize_raffled_query += f"&prize_raffled={prize_id}"
    if prize_raffled_query == "":   # 奖品为空
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="奖品不能为空")
    # 如果请求体中user_uuid为空（仅抽奖项目），则生成一个随机的user_uuid
    if not raffle_result.user_uuid:
        user_uuid = str(uuid1())
    # 如果请求体中user_uuid不为空，说明用户答过题了（问答+抽奖项目）已经生成过uuid，直接使用原来的uuid
    else:
        user_uuid = raffle_result.user_uuid
    claim_prize_url = \
        f"{WEBSITE_URL}/claim-prize?project_uuid={raffle_result.project_uuid}&user_uuid={user_uuid}" + prize_raffled_query
    qr_code_url = generate_qrcode(claim_prize_url, user_uuid + raffle_result.project_uuid)
    return {
        "project_uuid": raffle_result.project_uuid,
        "user_uuid": user_uuid,
        "qr_code_url": qr_code_url,
        "claim_prize_url": claim_prize_url
    }
