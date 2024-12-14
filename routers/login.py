from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Header
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


# class UsernameAlreadyExists(BaseModel):
#     detail: str = "Username already exists."
    

# class IncorrectUsernameOrPassword(BaseModel):
#     detail: str = "Incorrect username or password."


# class NotAuthorized(BaseModel):
#     detail: str = "Not authorized."



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
            description="Register a new user whatever manager or not, username must be unique.")
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
            description="Log in a user and get a token for further authentication.")
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


# class InvalidRefreshToken(BaseModel):
#     detail: str = "Invalid Refresh token."


@router.get("/refresh/token", response_model=Token,
            responses={401: {"description": "Invalid Refresh token."}},
            description="""
            When access token expires, use refresh token to get a new access token. 
            The method is to place the refresh token in the header with key "Authorization" 
            and value "Bearer <refresh_token>" like using an access token.
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


@router.get("/user/me/", response_model=sch.UserResponse,
            responses={401: {"description": "Not authorized."}},
            description="Get the current logined user's information.")
async def get_current_user(user = Depends(verify_token)):
    return user
    

@router.delete("/user/me/", status_code=status.HTTP_204_NO_CONTENT,
            responses={
                401: {"description": "Not authorized."}},
            description="Delete the current logined user's account.")
async def delete_current_user(user = Depends(verify_token), session: Session = Depends(get_session)):
    session.delete(user)
    session.commit()

