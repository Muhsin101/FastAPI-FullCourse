from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy.orm import Session
from typing import Annotated
from ..models import Todos
from ..database import SessionLocal
from .auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="TodoApp/templates")

# creates APIRouter instance
# allows route grouping
# is included in the main FastAPI app
router = APIRouter(
    prefix='/todos',
    tags=['todos']
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

# defines a request schema for creating + updating todos
# inherits from BaseModel, meaning it's a pydantic model with automatic validation
class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response

### Pages ###

@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()

        todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()

        return templates.TemplateResponse("todo.html", {"request": request, "todos": todos, "user": user})

    except:
        return redirect_to_login()

@router.get("/add-todo-page")
async def render_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})

    except:
        redirect_to_login()

@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        todo = db.query(Todos).filter(Todos.id == todo_id).first()

        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})

    except:
        redirect_to_login()

### Endpoints ###

# defines a get route at the root '/' of the route + returns 200 ok status
# async allows the code to carry on while the function loads its data
# queries the todos table and returns all records
# queries = sending a request to db to retrieve, insert, update, or delete
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()

# takes todo_id as a path parameter which must be greater than 0
# queries the todos table for specific todo_id
# checks if a todos with the given todo_id exists
    # return it if it does
    # if not it raises an error
@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()

    if todo_model is not None:
        return todo_model

    raise HTTPException(status_code=404, detail='Todo not found')

# defines a post route for creating a new todos + returns 201 created status
# converts todo_request pydantic model into a todos model using model_dump()
# adds the new todo_model to db session
# commits the transaction to save new todos to db
#
@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get('id'))

    db.add(todo_model)
    db.commit()

@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')


    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found')

    db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).delete()
    db.commit()



