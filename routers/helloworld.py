from fastapi import APIRouter

router = APIRouter()


@router.get('/')
def hello_world():
    return {'message': 'Hello World!'}