from pydantic import BaseModel, Field
from starlette import status
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Annotated
from models import Users
from database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext

# creates APIRouter instance
# allows route grouping
# is included in the main FastAPI app
router = APIRouter(
prefix='/user',
    tags=['user']
)


def get_db():
    # creates new db session
    db = SessionLocal()
    # yields the db session for use in routes
    # yields = making a function into a generator = special function that can be paused and resumed , allowing production of values over time
    try:
        yield db
    # ensures db session is closed after the route handler is finished
    finally:
        db.close()

# annotated = type hint that allows you to add metadata to types
# used to give more information about the type without affecting the behaviour
# type of db_dependency = Session which is obtained through dependency injection
# db_dependency - dependency injection - do something before executing desired code
# a way to declare things that are required for app/func to work by injecting dependencies
db_dependency = Annotated[Session, Depends(get_db)]

#
user_dependency = Annotated[dict, Depends(get_current_user)]

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)

@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    return db.query(Users).filter(Users.id == user.get('id')).first()

@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None:
        HTTPException(status_code=401, detail='Authentication Failed')

    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail='Error on password change')

    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()

@router.put("/phonenumber/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def change_phone_number(user: user_dependency, db: db_dependency, phone_number: str):
    if user is None:
        HTTPException(status_code=401, detail='Authentication Failed')

    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    user_model.phone_number == phone_number
    db.add(user_model)
    db.commit()

