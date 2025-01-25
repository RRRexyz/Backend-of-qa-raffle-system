from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, status, Query, Path
from utils.authorization import verify_token
from sqlmodel import Session, select
import utils.schemas as schemas
from sql.database import get_session
import sql.models as models
from uuid import uuid1
from datetime import datetime
from ast import literal_eval
from pydantic import ValidationError
from utils.globalvar import WEBSITE_URL, SERVER_URL
from utils.qrcode import generate_qrcode
import os


router = APIRouter()


@router.post("/project/test", response_model=schemas.ProjectDetailResponse,
            response_description="项目创建成功，返回项目详细信息",
            summary="创建项目", 
            deprecated=True)
async def create_project_test(project_create: schemas.ProjectCreate,
                        session: Session = Depends(get_session),
                        creater = Depends(verify_token)):
    """已弃用，请使用`/project`接口
    """
    project_dict = project_create.model_dump()
    if project_dict.get("questions") == [] and project_dict.get("prizes") == []:
        project_type = 0 # 空项目
    elif project_dict.get("questions") == [] and project_dict.get("prizes") != []:
        project_type = 1 # 仅抽奖项目
    elif project_dict.get("questions") != [] and project_dict.get("prizes") == []:
        project_type = 2 # 仅问卷项目
    elif project_dict.get("questions") != [] and project_dict.get("prizes") != []:
        project_type = 3 # 问答+抽奖项目
    else:
        project_type = -1 # 未知项目类型
    project_uuid = str(uuid1())
    project = models.Project.model_validate(
        project_dict, 
        update={
            "uuid": str(project_uuid),
            "project_type": project_type,
            "creater_id": creater.id
                })
    session.add(project)
    session.commit()
    session.refresh(project)
    for question in project_dict.get("question"):
        question_into_db = models.Question.model_validate(
            question, 
            update={"project_uuid": project_uuid})
        session.add(question_into_db)
        session.commit()
        session.refresh(question_into_db)
    for prize in project_dict.get("prize"):
        print(prize.get("amount"))
        prize_into_db = models.Prize.model_validate(
            prize, 
            update={
                "project_uuid": project_uuid,
                "remain": prize.get("amount")
                })
        session.add(prize_into_db)
        session.commit()
        session.refresh(prize_into_db)
    return project


@router.post("/project", status_code=status.HTTP_201_CREATED,
            response_model=schemas.ProjectCreateResponse,
            response_description="项目创建成功，返回项目uuid",
            responses={400: {"description": "项目问答或抽奖格式错误"},
                        401: {"description": "未获得授权"}},
            summary="创建项目")
async def create_project(
        name: str = Form(examples=["毕业跑"], description="项目名称"),
        description: str | None = Form(default=None, examples=["毕业跑展台活动"], description="项目描述"),
        start_time: datetime = Form(examples=["2025-02-01 10:00:00"],
                                    description="项目开始时间，格式为YYYY-MM-DD HH:MM:SS，必须早于截止时间"),
        dead_line: datetime = Form(examples=["2025-03-15 14:00:00"],
                                    description="项目截止时间，格式为YYYY-MM-DD HH:MM:SS，必须晚于开始时间"),
        question: str = Form(default="[]",
            examples=["""[
    {
        "q": "山东大学是什么时候成立的？",
        "o1": "1900",
        "o2": "1901",
        "o3": "1902",
        "o4": "1903",
        "a": 2
    },
        {
        "q": "山东大学是什么时候成立的？",
        "o1": "1900",
        "o2": "1901",
        "o3": "1902",
        "o4": "1903",
        "a": 2
    },
        {
        "q": "山东大学是什么时候成立的？",
        "o1": "1900",
        "o2": "1901",
        "o3": "1902",
        "o4": "1903",
        "a": 2
    }
]"""], description="""添加的所有问答组成的JSON数组并转换为字符串格式，数组中每个JSON对象中应该包含以下字段：
- **q**: 问题，字符串
- **o1**: 选项1，字符串
- **o2**: 选项2，字符串
- **o3**: 选项3，字符串
- **o4**: 选项4，字符串
- **a**: 正确答案，整数，1-4对应选项1-4，也对应页面上的A-D

也就是形如`[{"q": "山东大学是什么时候成立的？","o1": "1900","o2": "1901","o3": "1902",
"o4": "1903","a": 2}]`的字符串，在JS中只要定义一个数组，然后用JSON.stringify()方法转换为字符串即可。
        """),
        prize: str = Form(default="[]", examples=["""[
    {
        "name": "帆布包",
        "level": 1,
        "amount": 100,
    },
    {
        "name": "手机支架",
        "level": 2,
        "amount": 200,
    },
    {
        "name": "学线书签",
        "level": 3,
        "amount": 300,
    }
]"""], description="""添加的所有抽奖项目的JSON数组并转换为字符串格式，数组中每个JSON对象中应该包含以下字段:
- **name**: 奖品名称，字符串
- **level**: 奖品等级，整数，是几就是几等奖
- **amount**: 奖品数量（总量），整数，总共可以发多少个奖品

格式同question。
        """),
        images: list[UploadFile] = File(default_factory=list, 
                                        description="""奖品图片文件组成的数组，按照奖品顺序排列。

比如说，如果一共有3种奖品，索引分别为0、1、2（从0开始），第0种奖品有图片，第1种奖品没有图片，第2种奖品有图片，
则数组中先后添加第0个奖品的图片文件、第2个奖品的图片文件。
        """),
        image_index: str = Form(default="[]", examples=["[0, 2]"],
                                description="""包含图片的奖品的索引数组并转换成字符串格式，按照奖品顺序排列。
                                    
比如说，如果一共有3种奖品，索引分别为0、1、2（从0开始），第0种奖品有图片，第1种奖品没有图片，第2种奖品有图片，
则应该输入`[0, 2]`形式的字符串。
        """),
        prize_claim_way: int | None = Form(default=None, examples=[1], 
                                        description="兑奖方式：0-抽奖现场兑奖，1-指定地点兑奖"),
        correct_item_num: int | None = Form(default=None, examples=[5],
                                        description="获得抽奖机会至少需要答对的题目数量，\
                                        数值必须小于或等于题目总数（前端校验）， \
                                        在问答+抽奖项目中给出"),
        total_raffle_times: int | None = Form(default=None, examples=[4],
                                            description="可抽奖次数，在仅抽奖项目中给出"),
        prize_claim_place: str | None = Form(default=None, examples=["展台现场"],
                                            description="奖品兑奖地点，在指定地点兑奖项目中给出"),
        prize_claim_time: str | None = Form(default=None, examples=["周五晚7-9点"],
                                            description="奖品兑奖时间，让用户自由输入即可，不用限制格式，\
                                            在指定地点兑奖项目中给出"),
        creater = Depends(verify_token),
        session: Session = Depends(get_session)
):
    """需要验证token
    """
    question_list = literal_eval(question) # str -> list
    prize_list = literal_eval(prize)
    try:    # 先对问答和奖品格式进行验证
        for question_dict in question_list:
            schemas.QuestionCreate.model_validate(question_dict)
        for prize_dict in prize_list:
            schemas.PrizeCreate.model_validate(prize_dict)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目问答或抽奖格式错误")
    if question_list == [] and prize_list == []:
        project_type = 0 # 空项目
    elif question_list == [] and prize_list != []:
        project_type = 1 # 仅抽奖项目
    elif question_list != [] and prize_list == []:
        project_type = 2 # 仅问卷项目
    elif question_list != [] and prize_list != []:
        project_type = 3 # 问答+抽奖项目
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目问答或抽奖格式错误")
    project_uuid = str(uuid1())
    now_time = datetime.now()
    if now_time < start_time:
        project_status = 0 # 未开始
    elif now_time > dead_line:
        project_status = 2 # 已结束
    else:
        project_status = 1 # 进行中
    project = models.Project(
        uuid = str(project_uuid),
        name = name,
        start_time = start_time,
        dead_line = dead_line,
        description = description,
        status=project_status,
        project_type = project_type,
        prize_claim_way = prize_claim_way,
        correct_item_num = correct_item_num,
        total_raffle_times = total_raffle_times,
        prize_claim_place = prize_claim_place,
        prize_claim_time = prize_claim_time,
        creater_id = creater.id
        )
    session.add(project)
    session.commit()
    session.refresh(project)
    for question in question_list:
        question_into_db = models.Question.model_validate(
            question, 
            update={"project_uuid": project_uuid})
        session.add(question_into_db)
        session.commit()
        session.refresh(question_into_db)
    image_index = literal_eval(image_index) # str -> list
    for i in range(len(prize_list)):
        if i in image_index:    # 奖品有图片
            ii = image_index.index(i)   # 图片在images中的索引
            filename = str(uuid1()) + images[ii].filename  # 在文件名前加一个随机的uuid，防止文件名出现重复冲突
            with open(f"static/{filename}", "wb") as f:
                f.write(images[ii].file.read())
            prize_into_db = models.Prize.model_validate(
                prize_list[i], 
                update={
                    "project_uuid": project_uuid,
                    "remain": prize_list[i].get("amount"),
                    "image": f"{SERVER_URL}/static/{filename}"
                    })
        else:   # 奖品无图片
            prize_into_db = models.Prize.model_validate(
                prize_list[i], 
                update={
                    "project_uuid": project_uuid,
                    "remain": prize_list[i].get("amount")
                    })
        session.add(prize_into_db)
        session.commit()
        session.refresh(prize_into_db)
    return {"project_uuid": project_uuid}


@router.put("/project/{project_uuid}", 
            response_model=schemas.ProjectCreateResponse,
            response_description="项目编辑成功，返回项目uuid",
            responses={400: {"description": "项目问答或抽奖格式错误"},
                        401: {"description": "未获得授权"}},
            summary="编辑项目")
async def edit_project(
        project_uuid: str = Path(description="项目uuid"),
        name: str = Form(examples=["毕业跑"], description="项目名称"),
        description: str | None = Form(default=None, examples=["毕业跑展台活动"], description="项目描述"),
        start_time: datetime = Form(examples=["2025-02-01 10:00:00"],
                                    description="项目开始时间，格式为YYYY-MM-DD HH:MM:SS"),
        dead_line: datetime = Form(examples=["2025-03-15 14:00:00"],
                                    description="项目截止时间，格式为YYYY-MM-DD HH:MM:SS"),
        question: str = Form(default="[]",
            examples=["""[
    {
        "q": "山东大学是什么时候成立的？",
        "o1": "1900",
        "o2": "1901",
        "o3": "1902",
        "o4": "1903",
        "a": 2
    },
    {
        "q": "山东大学是什么时候成立的？",
        "o1": "1900",
        "o2": "1901",
        "o3": "1902",
        "o4": "1903",
        "a": 2
    },
    {
        "q": "山东大学是什么时候成立的？",
        "o1": "1900",
        "o2": "1901",
        "o3": "1902",
        "o4": "1903",
        "a": 2
    }
]"""], 
            description="""添加的所有问答组成的JSON数组并转换为字符串格式，数组中每个JSON对象中应该包含以下字段：
- **q**: 问题，字符串
- **o1**: 选项1，字符串
- **o2**: 选项2，字符串
- **o3**: 选项3，字符串
- **o4**: 选项4，字符串
- **a**: 正确答案，整数，1-4对应选项1-4，也对应页面上的A-D

也就是形如`[{"q": "山东大学是什么时候成立的？","o1": "1900","o2": "1901","o3": "1902",
"o4": "1903","a": 2}]`的字符串，在JS中只要定义一个数组，然后用JSON.stringify()方法转换为字符串即可。
        """),
        prize: str = Form(default="[]", examples=["""[
    {
        "name": "帆布包",
        "level": 1,
        "amount": 100,
        "remain": 90
    },
    {
        "name": "手机支架",
        "level": 2,
        "amount": 200,
        "remain": 180
    },
    {
        "name": "学线书签",
        "level": 3,
        "amount": 300,
        "remain": 270
    }
]"""], description="""添加的所有抽奖项目的JSON数组并转换为字符串格式，数组中每个JSON对象中应该包含以下字段:
- **name**: 奖品名称，字符串
- **level**: 奖品等级，整数，是几就是几等奖
- **amount**: 奖品数量（总量），整数，总共可以发多少个奖品
- **remain**: 奖品剩余数量，整数，剩余可发多少个奖品（前端根据管理员对奖品数量的修改计算出）

格式同question。
        """),
        images: list[UploadFile] = File(default_factory=list, 
                                        description="""奖品图片文件组成的数组，按照奖品顺序排列。

比如说，如果一共有3种奖品，索引分别为0、1、2（从0开始），第0种奖品有图片，第1种奖品没有图片，第2种奖品有图片，
则数组中先后添加第0个奖品的图片文件、第2个奖品的图片文件。
        """),
        image_index: str = Form(default="[]", examples=["[0, 2]"],
                                description="""包含图片的奖品的索引数组并转换成字符串格式，按照奖品顺序排列。
                                    
比如说，如果一共有3种奖品，索引分别为0、1、2（从0开始），第0种奖品有图片，第1种奖品没有图片，第2种奖品有图片，
则应该输入`[0, 2]`形式的字符串。
        """),
        prize_claim_way: int | None = Form(default=None, examples=[1], 
                                        description="兑奖方式：0-抽奖现场兑奖，1-指定地点兑奖"),
        correct_item_num: int | None = Form(default=None, examples=[5],
                                        description="获得抽奖机会至少需要答对的题目数量，\
                                        数值必须小于或等于题目总数（前端校验）， \
                                        在问答+抽奖项目中给出"),
        total_raffle_times: int | None = Form(default=None, examples=[4],
                                            description="可抽奖次数，在仅抽奖项目中给出"),
        prize_claim_place: str | None = Form(default=None, examples=["展台现场"],
                                            description="奖品兑奖地点，在指定地点兑奖项目中给出"),
        prize_claim_time: str | None = Form(default=None, examples=["周五晚7-9点"],
                                            description="奖品兑奖时间，让用户自由输入即可，不用限制格式，\
                                            在指定地点兑奖项目中给出"),
        creater = Depends(verify_token),
        session: Session = Depends(get_session)
):
    """需要验证token
    """
    project = session.get(models.Project, project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if project.creater_id != creater.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未获得授权")
    # 删除原有项目的奖品照片
    prizes = session.exec(select(models.Prize).filter_by(project_uuid=project_uuid)).all()
    for prize_in_db in prizes:
        if prize_in_db.image:
            image_path = prize_in_db.image.replace(f"{SERVER_URL}/", "")
            os.remove(image_path)
    # 删除原有项目
    session.delete(project) 
    session.commit()
    # 按更新后的信息重新创建项目，但project_uuid不变
    question_list = literal_eval(question) # str -> list
    prize_list = literal_eval(prize) # 这里错了
    try:    # 先对问答和奖品格式进行验证
        for question_dict in question_list:
            schemas.QuestionCreate.model_validate(question_dict)
        for prize_dict in prize_list:
            schemas.PrizeCreate.model_validate(prize_dict)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目问答或抽奖格式错误")
    if question_list == [] and prize_list == []:
        project_type = 0 # 空项目
    elif question_list == [] and prize_list != []:
        project_type = 1 # 仅抽奖项目
    elif question_list != [] and prize_list == []:
        project_type = 2 # 仅问卷项目
    elif question_list != [] and prize_list != []:
        project_type = 3 # 问答+抽奖项目
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目问答或抽奖格式错误")
    # project_uuid = str(uuid1())
    now_time = datetime.now()
    if now_time < start_time:
        project_status = 0 # 未开始
    elif now_time > dead_line:
        project_status = 2 # 已结束
    else:
        project_status = 1 # 进行中
    project = models.Project(
        uuid = project_uuid,
        name = name,
        start_time = start_time,
        dead_line = dead_line,
        description = description,
        status = project_status,
        project_type = project_type,
        prize_claim_way = prize_claim_way,
        correct_item_num = correct_item_num,
        total_raffle_times = total_raffle_times,
        prize_claim_place = prize_claim_place,
        prize_claim_time = prize_claim_time,
        creater_id = creater.id
        )
    session.add(project)
    session.commit()
    session.refresh(project)
    for question in question_list:
        question_into_db = models.Question.model_validate(
            question, 
            update={"project_uuid": project_uuid})
        session.add(question_into_db)
        session.commit()
        session.refresh(question_into_db)
    image_index = literal_eval(image_index) # str -> list
    for i in range(len(prize_list)):
        if i in image_index:    # 奖品有图片
            ii = image_index.index(i)   # 图片在images中的索引
            filename = str(uuid1()) + images[ii].filename  # 在文件名前加一个随机的uuid，防止文件名出现重复冲突
            with open(f"static/{filename}", "wb") as f:
                f.write(images[ii].file.read())
            prize_into_db = models.Prize.model_validate(
                prize_list[i], 
                update={
                    "project_uuid": project_uuid,
                    "image": f"{SERVER_URL}/static/{filename}"
                    })
        else:   # 奖品无图片
            prize_into_db = models.Prize.model_validate(
                prize_list[i], 
                update={
                    "project_uuid": project_uuid
                    })
        session.add(prize_into_db)
        session.commit()
        session.refresh(prize_into_db)
    return {"project_uuid": project_uuid}
    
    

@router.delete("/project/{project_uuid}", status_code=status.HTTP_204_NO_CONTENT,
            response_description="删除成功",
            responses={401: {"description": "未获得授权"},
                    404: {"description": "项目不存在"}},
            summary="删除项目")
async def delete_project(project_uuid: str = Path(description="项目uuid"),
                        session: Session = Depends(get_session),
                        creater = Depends(verify_token)):
    """删除一个项目及其所有的相关信息，包括问答、奖品、记录、二维码等。
    
    需要验证token
    """
    project = session.get(models.Project, project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if project.creater_id != creater.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未获得授权")
    # 删除项目二维码
    if project.qr_code:
        qr_code_path = f"static/{project_uuid}.png"
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)
    # 删除奖品图片
    prizes = session.exec(select(models.Prize).filter_by(project_uuid=project_uuid)).all()
    for prize in prizes:
        if prize.image:
            image_path = prize.image.replace(f"{SERVER_URL}/", "")
            if os.path.exists(image_path):
                os.remove(image_path)
    # 删除未兑奖的兑奖二维码
    all_files = os.listdir(f"static")
    for file in all_files:
        if file.endswith(f"{project_uuid}.png"):
            os.remove(file)
    # 删除项目
    session.delete(project)
    session.commit()



@router.get("/projects",
            response_model=list[schemas.MyProjectPreview],
            response_description="返回当前账号的所有项目预览列表",
            summary="获取当前账号的所有项目预览列表")
async def get_project_preview_list(user = Depends(verify_token),
                                session: Session = Depends(get_session)):
    """需要验证token
    """
    projects = session.exec(select(models.Project).filter_by(creater_id=user.id)).all()
    projects_response = []
    for project in projects:
        qa_records = session.exec(select(models.Record).filter_by(project_uuid=project.uuid, 
                                                                record_type=1)).all()
        qa_total_correct_rate = 0.0
        for record in qa_records:
            qa_total_correct_rate += record.correct_rate
        qa_average_correct_rate = qa_total_correct_rate / len(qa_records) if len(qa_records) > 0 else 0.0
        project_dict = project.model_dump()
        project_dict["qa_average_correct_rate"] = qa_average_correct_rate
        projects_response.append(project_dict)
    return projects_response


@router.get("/projects/all",
            dependencies=[Depends(verify_token)],
            response_model=list[schemas.AllProjectPreview],
            response_description="返回所有账号的所有项目预览列表",
            summary="获取所有账号的所有项目预览列表")
async def get_all_project_list(session: Session = Depends(get_session)):
    """需要验证token
    """
    projects = session.exec(select(models.Project)).all()
    projects_response = []
    for project in projects:
        qa_records = session.exec(select(models.Record).filter_by(project_uuid=project.uuid, 
                                                                record_type=1)).all()
        qa_total_correct_rate = 0.0
        for record in qa_records:
            qa_total_correct_rate += record.correct_rate
        qa_average_correct_rate = qa_total_correct_rate / len(qa_records) if len(qa_records) > 0 else 0.0
        project_dict = project.model_dump()
        project_dict["qa_average_correct_rate"] = qa_average_correct_rate
        creater = session.get(models.User, project.creater_id)
        project_dict.update({"creater": creater.model_dump()})
        projects_response.append(project_dict)
    return projects_response


@router.get("/project/{project_uuid}",
            dependencies=[Depends(verify_token)],
            response_model=schemas.ProjectDetailResponse,
            response_description="返回项目详情",
            responses={401: {"description": "未获得授权"},
                    404: {"description": "项目不存在"}},
            summary="获取项目详情")
async def get_project_detail(project_uuid: str = Path(description="项目uuid"),
                            session: Session = Depends(get_session)):
    """需要验证token
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
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.post("/qrcode/project/{project_uuid}",response_model=schemas.ProjectQRCodeResponse,
            response_description="返回生成的二维码URL",
            responses={401: {"description": "未获得授权"},
                    404: {"description": "项目不存在"}},
            summary="生成参与项目用的二维码")
async def generate_project_qrcode(project_uuid: str = Path(description="项目UUID",
                                                        examples=["1820380e-22d0-4f68-97ed-bd49f563100b"]),
                                session: Session = Depends(get_session),
                                creater = Depends(verify_token)):
    """管理员在项目详情页面点击“生成二维码”按钮时调用此接口生成项目二维码，并返回生成的二维码URL。

二维码首次生成后会存入数据库，后续再次生成时直接返回数据库中保存的URL。
    
需要验证token
    """
    project = session.get(models.Project, project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if project.creater_id != creater.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未获得授权")
    if project.qr_code: # 如果二维码已经生成过，直接返回
        qr_code_url = project.qr_code
        project_url = f"{WEBSITE_URL}/project/{project_uuid}"
    else:    # 否则生成二维码并返回
        project_url = f"{WEBSITE_URL}/project/{project_uuid}"
        qr_code_url = generate_qrcode(project_url, project_uuid)
        project.qr_code = qr_code_url
        session.add(project)
        session.commit()
        session.refresh(project)
    return {
        "qr_code_url": qr_code_url,
        "project_participate_url": project_url
        }


@router.get("/claim-prize", response_model=schemas.ClaimPrizeInfo,
            response_description="返回用户中奖信息及是否已兑奖", 
            dependencies=[Depends(verify_token)],   
            responses={404: {"description": "奖品不存在"},
                        401: {"description": "未获得授权"}},
            summary="扫兑奖码返回用户中奖信息及是否已兑奖")
async def get_claim_prize_info(
                project_uuid: str = Query(description="项目UUID",
                                            examples=["1820380e-22d0-4f68-97ed-bd49f563100b"]),
                user_uuid: str = Query(description="用户UUID",
                                            examples=["2fcfa550-d93b-11ef-a2a9-832c32728689"]),
                prize_raffled: list[int] = Query(description="抽中奖品的id数组",
                                            examples=["[1, 2, 3]"]),
                session: Session = Depends(get_session)):
    """扫描兑奖码进入兑奖信息界面后，调用此接口返回用户中奖信息及是否已兑奖。
    
    如果`claim_prize_status`为`False`，则表示用户未兑奖，显示兑奖按钮。
    
    如果`claim_prize_status`为`True`，则表示用户已兑奖，不要显示兑奖按钮。
    
    需要验证token
    """
    # 先查询用户是否已经兑奖
    record = session.exec(select(models.Record).filter_by(project_uuid=project_uuid, 
                                                        participant_uuid=user_uuid,
                                                        record_type=2)).first()
    if not record:  
        claim_prize_status = False
    else:
        claim_prize_status = True
    # 再查询奖品信息
    prizes = []
    for prize_id in prize_raffled:
        prize = session.get(models.Prize, prize_id)
        if not prize:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="奖品不存在")
        prizes.append(prize)
    return  {          
        "claim_prize_status": claim_prize_status,
        "prizes": prizes
    }


@router.post("/claim-prize", status_code=status.HTTP_201_CREATED,
            response_model=schemas.ClaimPrizeInfo,
            response_description="返回已兑奖信息",    
            dependencies=[Depends(verify_token)], 
            responses={401: {"description": "未获得授权"},
                        404: {"description": "项目不存在"}},
            summary="给用户兑奖")
async def claim_prize(claim_prize_submit: schemas.ClaimPrizeSubmit,
                    session: Session = Depends(get_session)):
    """调用后在数据库中创建一条兑奖记录，并返回已兑奖信息，随后会删除图床中的兑奖二维码。
    
    需要验证token
    """
    project = session.get(models.Project, claim_prize_submit.project_uuid)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    claim_record = models.Record(participant_uuid=claim_prize_submit.user_uuid,
                                project_uuid=claim_prize_submit.project_uuid,
                                record_type=2) # 2表示兑奖记录
    session.add(claim_record)    
    session.commit()
    session.refresh(claim_record)
    # 删除图床中的兑奖二维码
    os.remove(f"static/{claim_prize_submit.user_uuid}{claim_prize_submit.project_uuid}.png")
    return {
        "claim_prize_status": True
    }
    



