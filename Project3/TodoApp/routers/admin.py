from pydantic import BaseModel, Field
from starlette import status
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Annotated
from models import Todos
from database import SessionLocal
from .auth import get_current_user

# creates APIRouter instance
# allows route grouping
# is included in the main FastAPI app
router = APIRouter(
prefix='/admin',
    tags=['admin']
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


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication failed')
    return db.query(Todos).all()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delet_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication failed')
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found')
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()