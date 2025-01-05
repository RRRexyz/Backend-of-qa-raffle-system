from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

import schemas as sch
from sql.database import Session, get_session
import sql.models as models

from sqlalchemy.exc import IntegrityError
from sqlmodel import select


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "3d6514c1a732ba8054ba5c0c6194fd6e31fb287bdb3137534ea74f4c1a2f7138"
ALGORITHM = "HS256"


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    username: str


class TokenData(BaseModel):
    username: str | None = None



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: Annotated[str, Depends(oauth2_scheme)], 
                session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = session.exec(select(models.User).filter_by(username=token_data.username)).first()
    if not user:
        raise credentials_exception
    return user


@router.post("/register", response_model=sch.UserResponse, 
            status_code=status.HTTP_201_CREATED,
            responses = {400: {"description": "Username already exists."}},
            summary="注册一个新用户（普通用户或管理员），用户名必须唯一",
            description="""
管理员可以创建、查看、更新和删除项目，而普通用户只能查看和参与项目。

`qq`和`phone`字段可选。
""")
async def register_user(user: sch.UserRegister, session: Session = Depends(get_session)):
    user_for_db = models.User(username=user.username, 
                            hashed_password=get_password_hash(user.password),
                            manage_permission=user.manage_permission,
                            qq=user.qq,
                            phone=user.phone)
    try:
        session.add(user_for_db)
        session.commit()
        session.refresh(user_for_db)
    except IntegrityError: 
        raise HTTPException(status_code=400, detail="Username already exists.")
    return user_for_db


@router.post("/login", response_model=Token, 
            responses={401: {"description": "Incorrect username or password."}},
            summary="""
登录账号并获取 access token 和 refresh token。
""")
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                    session: Session = Depends(get_session)) -> Token:
    user = session.exec(select(models.User).filter_by(username=form_data.username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"})
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    return Token(access_token=access_token, refresh_token=refresh_token,
                token_type="bearer", username=user.username)


@router.patch("/user/me", response_model=sch.UserResponse,
            responses={401: {"description": "Not authorized."},
                    404: {"description": "User not found."}},
            summary="更新当前登录用户的信息。",
            description="""
可改项包括`username`、`qq`、`phone`。
""")
async def update_user(user_update: sch.UserUpdate, 
                    user = Depends(verify_token), 
                    session: Session = Depends(get_session)):
    user = session.get(models.User, user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found.")
    user_data = user_update.model_dump(exclude_unset=True)
    user.sqlmodel_update(user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.patch("/user/password",
            responses={401: {"description": "Incorrect username or password."},
                    404: {"description": "User not found."}},
            summary="用户更改密码。",
            description="""
不需要登录，只需提供用户名、原密码和新密码。
""")
async def change_password(username: str = Form(), 
                        old_password: str = Form(), 
                        new_password: str = Form() ,
                        session: Session = Depends(get_session)):
    user = session.exec(select(models.User).filter_by(username=username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found.")
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"})
    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    

@router.get("/refresh/token", response_model=Token,
            responses={401: {"description": "Invalid Refresh token."}},
            summary="当access_token过期时，用refresh_token获取新的access_token",
            description="""
方法是在请求头添加`Authorization`字段并设置值为`Bearer <refresh_token>`。
""")
async def refresh_token(refresh_token: Annotated[str, Depends(oauth2_scheme)], 
                session: Session = Depends(get_session)):
    refresh_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Refresh token.",
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


@router.get("/user/me", response_model=sch.UserResponse,
            responses={401: {"description": "Not authorized."}},
            summary="获取当前登录用户的信息。")
async def get_current_user(user = Depends(verify_token)):
    return user
    

@router.delete("/user/me", status_code=status.HTTP_204_NO_CONTENT,
            responses={401: {"description": "Not authorized."}},
            summary="谨慎：注销当前登录用户的账号。")
async def delete_current_user(user = Depends(verify_token), session: Session = Depends(get_session)):
    session.delete(user)
    session.commit()

