from fastapi import APIRouter, Depends, status
import schemas as sch 
import sql.crud as crud
from routers.login import verify_token


router = APIRouter()


@router.post("/project", response_model=sch.ProjectResponse,
            status_code=status.HTTP_201_CREATED,
            responses={
                401: {"description": "Not authorized."},
                403: {"description": "No permission."}})
async def create_qa(project = Depends(crud.create_project)):
    return project  


@router.get("/project/me", response_model=list[sch.ProjectResponse],
            responses={401: {"description": "Not authorized."}},
            description="Get all the projects created by the logined user.This may used \
            to display the project preview on the home page.")
async def get_my_qa(projects = Depends(crud.read_projects_by_manager)):
    return projects


@router.get("/project/{project_id}", response_model=sch.ProjectWithQuestions,
            responses={401: {"description": "Not authorized."},
                        404: {"description": "Project not found."}},
            dependencies=[Depends(verify_token)],
            description="Get a project's detail information.")
async def get_project_details(project = Depends(crud.read_project_details)):
    return project


@router.post("/question", response_model=sch.QuestionResponse,
            status_code=status.HTTP_201_CREATED,
            responses={401: {"description": "Not authorized."}},
            description="Create a new question for a qa project.")
async def add_question(question = Depends(crud.add_question)):
    return question