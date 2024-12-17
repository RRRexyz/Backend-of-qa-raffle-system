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
# Create a new empty qa project.

After creating a new project, it will be unpublished status.(`status=0`)

You can add questions and prizes to the project and then publish it.(`status=1`)
""")
async def create_qa(project = Depends(crud.create_project)):
    return project  


@router.get("/project/me", response_model=list[sch.ProjectResponse],
            responses={401: {"description": "Not authorized."}},
            description="""
# Get all the projects (*withouth questions and prizes information*) created by the logined user.

This may used to display the project previews on the home page.
""")
async def get_my_qa(projects = Depends(crud.read_projects_by_manager)):
    return projects


@router.get("/project/{project_id}", response_model=sch.ProjectWithQuestions,
            responses={401: {"description": "Not authorized."},
                        404: {"description": "Project not found."}},
            dependencies=[Depends(verify_token)],
            description="""
# Get a project's detail information.

When users enter the project's detail page, use this API to load the information.
""")
async def get_project_details(project = Depends(crud.read_project_details)):
    return project


@router.post("/question", response_model=sch.QuestionResponse,
            status_code=status.HTTP_201_CREATED,
            responses={401: {"description": "Not authorized."}},
            description="""
# Create a new question for a qa project.

`a` is the answer of `q`, and the value 1, 2, 3, 4 represents 'A', 'B', 'C', 'D'.
""")
async def add_question(question = Depends(crud.add_question)):
    return question