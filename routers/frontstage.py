from fastapi import APIRouter, Depends, status
import schemas as sch 
import sql.crud as crud
from routers.login import verify_token

router = APIRouter()


@router.get("/projects/user", response_model=list[sch.ProjectResponse],
            responses={401: {"description": "Not authorized."}},
            summary="获取用户参与过的所有项目预览（不包含问答题目和抽奖奖品信息）。",
            description="""
用于在用户主页展示自己参与过的项目预览信息。
""")
async def get_records_by_user(projects = Depends(crud.read_records_by_user)):
    return projects


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

**对仅抽奖项目**：用户未抽奖时，返回抽奖次数`raffle_times`为`1`。用户有抽奖记录后，还会返回抽奖结果（抽奖次数为`0`）。

`raffle_result`为用户的抽奖结果，是一个存有用户每次抽奖获得的奖品的`id`的数组。
前端可以通过`id`获取奖品的具体信息。

`raffle_remain_times`为剩余抽奖次数，当`raffle_times`为`null`时，此字段也为`null`。

`raffle_time`为用户最新一次抽奖的时间，后端自动生成并更新。

""")
async def get_project_details(project = Depends(crud.read_project_details_by_user)):
    return project


@router.post("/answer", response_model=sch.ProjectWithQuestionsAndPrizesForUser,
            responses={401: {"description": "Not authorized."}},
            summary="提交答题。",
            description="""
`project_id`指定答题的项目。

`answer`是一个包含用户答案(1~4)的数组，数组的每一个元素分别对应一道题的答案。

调用此接口会在数据库中创建一条答题记录，并返回包含用户答案和题目正确答案的完整项目信息。
""")
async def answer_question(project = Depends(crud.answer_question)):
    return project


@router.post("/raffle/{project_id}", response_model=sch.ProjectWithQuestionsAndPrizesForUser,
            responses={401: {"description": "Not authorized."},
                    403: {"description": "Project has ended."},
                    404: {"description": "Project not found."}},
            summary="进行一次抽奖。",
            description="""
使用`id`指定要进行抽奖的项目。

前端发现所有奖品剩余均为0或者剩余抽奖次数为0时，应该让抽奖按钮失效。

调用此接口会在奖池中随机抽取一个奖品。

每种奖品每个用户只会抽到一次，当然安慰奖可以多次抽到。

调用此接口会将抽奖记录存入数据库中，并返回包含抽奖结果的完整项目信息。其中抽奖结果是一个包含每次抽中的奖品的`id`的数组。
""")
async def raffle_prize(project = Depends(crud.raffle_prize)):
    return project