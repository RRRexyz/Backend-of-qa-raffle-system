from fastapi import APIRouter, Depends, status
import schemas as sch 
import sql.crud as crud
from routers.login import verify_token

router = APIRouter()


@router.get("/project/{project_id}/user", 
            response_model=sch.ProjectWithQuestionsAndPrizesForUser,
            responses={401: {"description": "Not authorized."},
                    403: {"description": "Project not published."},
                    404: {"description": "Project not found."}},
            summary="获取一个项目的详细信息。",
            description="""
使用`id`指定要获取的项目。

当用户进入项目详情页时，用此接口展示项目的所有信息。

调用此接口会增加项目的访问次数`browse_times`。

**对仅问答项目**：用户未答题时，只返回问答的题目和选项。用户有答题记录后，还会返回用户作答的答案和正确答案。

**对问答+抽奖项目**：用户未答题时，只返回问答的题目和选项，抽奖次数`raffle_times`为`null`。
用户有答题记录后，还会返回用户作答的答案和正确答案，抽奖次数`raffle_times`为计算得出的整数。

**对仅抽奖项目**：用户未抽奖时，返回抽奖次数`raffle_times`为`1`。用户有抽奖记录后，还会返回抽奖结果。

""")
async def get_project_details(project = Depends(crud.read_project_details_by_user)):
    return project


@router.post("/answer", response_model=sch.ProjectWithQuestionsAndPrizesForUser,
            responses={401: {"description": "Not authorized."}},
            summary="提交答题并查看答题结果。",
            description="""
`project_id`指定答题的项目。

`answer`是一个包含用户答案(1~4)的数组，数组的每一个元素分别对应一道题的答案。

调用此接口会在数据库中创建一条答题记录，并返回包含用户答案和题目正确答案的完整项目信息。
""")
async def answer_question(project = Depends(crud.answer_question)):
    return project