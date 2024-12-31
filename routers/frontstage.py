from fastapi import APIRouter, Depends, status
import schemas as sch 
import sql.crud as crud
from routers.login import verify_token

router = APIRouter()


@router.get("/project/{project_id}/user", response_model=sch.ProjectWithQuestionsAndPrizes,
            responses={401: {"description": "Not authorized."},
                    403: {"description": "Project not published."},
                    404: {"description": "Project not found."}},
            dependencies=[Depends(verify_token)],
            summary="获取一个项目的详细信息。",
            description="""
使用`id`指定要获取的项目。

当用户进入项目详情页时，用此接口展示项目的所有信息。

调用此接口会增加项目的访问次数`browse_times`。
""")
async def get_project_details(project = Depends(crud.read_project_details_by_user)):
    return project