from fastapi import APIRouter, Depends, status
import schemas as sch 
import sql.crud as crud
from routers.login import NotAuthorized
from pydantic import BaseModel

router = APIRouter()


class NoPermission(BaseModel):
    detail: str = " No Permission."

@router.post("/qa", response_model=sch.ProjectResponse,
            status_code=status.HTTP_201_CREATED,
            responses={
                401: {"model": NotAuthorized},
                403: {"model": NoPermission}})
async def create_qa(project = Depends(crud.create_project)):
    return project  