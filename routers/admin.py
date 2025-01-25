from fastapi import APIRouter, status, Depends, HTTPException, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
import utils.schemas as schemas
import sql.models as models
from sql.database import get_session
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from utils.authorization import *
from utils.globalvar import WEBSITE_URL, SERVER_URL
import os


router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse,
            status_code=status.HTTP_201_CREATED,
            response_description="注册的用户信息，包含id，不包含密码",
            responses = {400: {"description": "用户名已存在"}},
            summary="注册一个管理员账户")
async def register_user(user: schemas.UserRegister, session: Session = Depends(get_session)):
    """内部接口，不对外暴露。
    """
    user_for_db = models.User(username=user.username, 
                            hashed_password=get_password_hash(user.password),
                            campus=user.campus,
                            department=user.department,
                            qq=user.qq,
                            wx=user.wx)
    try:
        session.add(user_for_db)
        session.commit()
        session.refresh(user_for_db)
    except IntegrityError: 
        raise HTTPException(status_code=400, detail="用户名已存在")
    return user_for_db


@router.post("/login", response_model=Token, 
            response_description="登录成功返回access_token和refresh_token",
            responses={401: {"description": "账号或密码错误"}},
            summary="""登录账号""")
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                    session: Session = Depends(get_session)) -> Token:
    """请求体中包含以下字段：
    - **username**: 用户名
    - **password**: 密码

    可能要包含的字段：
    - **grant_type**: 设置为`password`
    
    须以表单形式提交。
    """
    user = session.exec(select(models.User).filter_by(username=form_data.username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"})
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    return Token(access_token=access_token, refresh_token=refresh_token,
                token_type="bearer", username=user.username)


@router.get("/refresh/token", response_model=Token,
            response_description="返回新的access_token，而refresh_token原样返回",
            responses={401: {"description": "无效的身份验证凭据"}},
            summary="当access_token过期时，用refresh_token获取新的access_token")
async def refresh_token(refresh_token: Annotated[str, Depends(oauth2_scheme)], 
                session: Session = Depends(get_session)):
    """在请求头添加`Authorization`字段并设置值为`Bearer <refresh_token>`。"""
    refresh_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的身份验证凭据",
        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise refresh_token_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise refresh_token_exception
    user = session.exec(select(models.User).filter_by(username=token_data.username)).first()
    if not user:
        raise refresh_token_exception
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, refresh_token=refresh_token,
                username=user.username, token_type="bearer")


@router.get("/admin/me", response_model=schemas.UserResponse,
            response_description="当前登录用户的信息，包含id，不包含密码",
            responses={401: {"description": "未获得授权"}},
            summary="获取当前登录用户的信息")
async def get_current_user(user = Depends(verify_token)):
    """需要验证token"""
    return user
    

@router.delete("/admin/me", status_code=status.HTTP_204_NO_CONTENT,
            response_description="删除成功",
            responses={401: {"description": "未获得授权"}},
            summary="谨慎：注销当前登录用户的账号。")
async def delete_current_user(user = Depends(verify_token), session: Session = Depends(get_session)):
    """需要验证token
    
    删除当前登录用户的账号，包括该账号创建的所有项目相关的信息。
    """
    # 删除该管理员创建的所有项目以及相关数据
    projects = session.exec(select(models.Project).filter_by(creater_id=user.id)).all()
    for project in projects:
        # 删除项目二维码
        if project.qr_code:
            qr_code_path = f"static/{project.uuid}.png"
            if os.path.exists(qr_code_path):
                os.remove(qr_code_path)
        # 删除奖品图片
        prizes = session.exec(select(models.Prize).filter_by(project_uuid=project.uuid)).all()
        for prize in prizes:
            if prize.image:
                image_path = prize.image.replace(f"{SERVER_URL}/", "")
                if os.path.exists(image_path):
                    os.remove(image_path)
        # 删除未兑奖的兑奖二维码
        all_files = os.listdir(f"static")
        for file in all_files:
            if file.endswith(f"{project.uuid}.png"):
                os.remove(file)
        # 删除项目
        session.delete(project)
        session.commit()
    # 删除该管理员账号
    session.delete(user)
    session.commit()