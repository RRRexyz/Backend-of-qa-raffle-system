from fastapi import APIRouter, Depends, status
import schemas as sch 
import sql.crud as crud
from routers.login import verify_token


router = APIRouter()


@router.post("/project", response_model=sch.ProjectResponse,
            status_code=status.HTTP_201_CREATED,
            responses={
                401: {"description": "Not authorized."},
                403: {"description": "No permission."}},
            description="""
# 创建一个新的空白项目。

刚创建完的项目处于未发布状态(`status=0`)。

你可以添加问答题目和抽奖奖品，并发布项目(`status=1`)。

当超过截止时间`deadline`后，项目将过期(`status=2`)。
""")
async def create_qa(project = Depends(crud.create_project)):
    return project  


@router.get("/project/me", response_model=list[sch.ProjectResponse],
            responses={401: {"description": "Not authorized."}},
            description="""
# 获取当前用户创建的所有项目的预览（不包含问答题目和抽奖奖品信息）。

用于在用户主页展示自己创建的项目预览信息。
""")
async def get_my_qa(projects = Depends(crud.read_projects_by_manager)):
    return projects


@router.get("/project/{project_id}", response_model=sch.ProjectWithQuestions,
            responses={401: {"description": "Not authorized."},
                        404: {"description": "Project not found."}},
            dependencies=[Depends(verify_token)],
            description="""
# 通过id获取一个项目的详细信息。

当用户进入项目详情页时，用此接口展示项目的所有信息。
""")
async def get_project_details(project = Depends(crud.read_project_details)):
    return project


@router.post("/question", response_model=sch.QuestionResponse,
            status_code=status.HTTP_201_CREATED,
            responses={401: {"description": "Not authorized."}},
            description="""
# 给项目增加一个新的问答题目。

`a`是问题`q`的答案，值1、2、3、4分别代表'A'、'B'、'C'、'D'。
""")
async def add_question(question = Depends(crud.add_question)):
    return question