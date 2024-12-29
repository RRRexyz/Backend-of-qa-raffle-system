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
            summary="创建一个新的空白项目。",
            description="""
刚创建完的项目处于未发布状态(`status=0`)。

你可以添加问答题目和抽奖奖品，并发布项目(`status=1`)。

当超过截止时间`deadline`后，项目将过期(`status=2`)。

`name`和`description`为项目的名称和详细描述。`description`可为空。

截止时间`deadline`的格式为："2024-12-18 19:43:05"（不必给出微秒数，默认为0即可）。创建时间`create_time`后端自动生成。

这两个时间在数据库中存储的格式类似"2024-12-18 19:43:05.123456"，小数点后六位是微秒数。

一个比较奇怪的点是，在读取数据库返回的响应体中Python的datetime模块解析的结果与数据库中的存储格式有所不同。
时间中的空格被替换成了"T"，例如"2024-12-18T19:43:05.123456"。

并且当微秒为0时，Python的datetime模块返回的内容中不会显示微秒。例如
数据库中的"2025-01-01 03:04:05.000000"，Python的datetime模块解析结果为"2025-01-01T03:04:05"。
""")
async def create_project(project = Depends(crud.create_project)):
    return project  


@router.patch("/project/{project_id}", response_model=sch.ProjectWithQuestionsAndPrizes,
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."},
                        404: {"description": "Project not found."}},
            summary="更新一个项目的信息。",
            description="""
使用`id`指定要更新的项目。

可更新项为`name`、`description`、`deadline`，都为可选。

`deadline`的格式为："2024-12-19 19:49:33"（不必给出微秒数，默认为0即可）。
""")
async def update_project(project = Depends(crud.update_project)):
    return project


@router.delete("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT,
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."},
                        404: {"description": "Project not found."}},
            summary="谨慎：删除一个项目。",
            description="""
使用`id`指定要删除的项目。
""")
async def delete_project(project = Depends(crud.delete_project)):
    pass



@router.get("/project/me", response_model=list[sch.ProjectResponse],
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."}},
            summary="获取当前用户创建的所有项目的预览（不包含问答题目和抽奖奖品信息）。",
            description="""
用于在管理员主页展示自己创建的项目预览信息。
""")
async def get_my_projects(projects = Depends(crud.read_projects_by_manager)):
    return projects


@router.get("/project/{project_id}", response_model=sch.ProjectWithQuestionsAndPrizes,
            responses={401: {"description": "Not authorized."},
                    404: {"description": "Project not found."}},
            dependencies=[Depends(verify_token)],
            summary="获取一个项目的详细信息。",
            description="""
使用`id`指定要获取的项目。
            
当管理员进入项目详情页时，用此接口展示项目的所有信息。

调用此接口不会增加项目的访问次数。（管理员自己看没什么意义）
""")
async def get_project_details(project = Depends(crud.read_project_details)):
    return project


@router.post("/question", response_model=sch.QuestionResponse,
            status_code=status.HTTP_201_CREATED,
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."},},
            summary="给项目增加一个新的问答题目。",
            description="""
`o1`、`o2`、`o3`、`o4`分别为ABCD四个选项。

`a`是问题`q`的正确答案，值1、2、3、4分别代表'A'、'B'、'C'、'D'。
""")   
async def add_question(question = Depends(crud.add_question)):
    return question


@router.patch("/question/{question_id}", response_model=sch.QuestionResponse,
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."},
                        404: {"description": "Question not found."}},
            summary="对一个问答题目的内容进行修改。",
            description="""
使用`id`指定要更新的项目。
""")
async def update_question(question = Depends(crud.update_question)):
    return question


@router.delete("/question/{question_id}", status_code=status.HTTP_204_NO_CONTENT,
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."},
                        404: {"description": "Question not found."}},
            summary="谨慎：删除一个问答题目。",
            description="""
使用`id`指定要删除的题目。
""")
async def delete_question(question = Depends(crud.delete_question)):
    pass


@router.post("/prize", response_model=sch.PrizeResponse,
            status_code=status.HTTP_201_CREATED,
            responses={401: {"description": "Not authorized."}},
            summary="给项目增加一个抽奖奖品。",
            description="""
`name`为奖品名称。

`image`为奖品图片存储在图床中的url地址。

`level`为奖品等级，1为一等奖，2为二等奖，3为三等奖，以此类推......
0为安慰奖。可以为空，空表示只有一个等级的奖品，不必设置等级。

`amount`为奖品数量，大于0。（前端校验一下吧）
""")
async def add_prize(prize = Depends(crud.add_prize)):
    return prize


@router.patch("/prize/{prize_id}", response_model=sch.PrizeResponse,
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."},
                        404: {"description": "Prize not found."},
                        400: {"description": "Prize amount is less than already raffled."}},
            summary="对一个抽奖奖品的内容进行修改。",
            description="""
使用`id`指定要更新的奖品。
""")
async def update_prize(prize = Depends(crud.update_prize)):
    return prize


@router.delete("/prize/{prize_id}", status_code=status.HTTP_204_NO_CONTENT,
            responses={401: {"description": "Not authorized."},
                        403: {"description": "No permission."},
                        404: {"description": "Prize not found."}},
            summary="谨慎：删除一个抽奖奖品。",
            description="""
使用`id`指定要删除的奖品。
""")
async def delete_prize(prize = Depends(crud.delete_prize)):
    pass