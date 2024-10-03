from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

# creates new router for handling auth related routes
# prefix specifies all routes defined in this route will start with '/auth'
# tags help group and categorise routes in the API documentation(Swagger UI)
router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

# SK is the key used to sign and verify JWT tokens, kept secret
# alg cryptographic algorithm used for encoding the JWT
SECRET_KEY = '394268855315cd06ede08e040c13a86583eb0474744b889da346a718a8cd921d'
ALGORITHM = 'HS256'

# bcrypt is an instance of CryptContext configured to use the bcrypt hashing algorithm for the passwords
# oauth2 defines OAuth2 password flow for token based auth, the tokenUrl specifies the endpoint where the user will send username and password for JWT
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# pydantic model defines structure for the request body when creating a new user
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    surname: str
    password: str
    role: str

# pydantic model defines structure of the token response
class Token(BaseModel):
    access_token: str
    token_type: str

# handles the lifecycle of the db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# db_dependency - dependency injection - do something before executing desired code
# a way to declare things that are required for app/func to work by injecting dependencies
db_dependency = Annotated[Session, Depends(get_db)]

# function checks if user exists in db with username
# verifies the password matches to the stored one, using bcrypt_context.verify()
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

# creates a JWT for the authorised users
# encode is a dictionary prepared as the payload of the JWT
# exp is the expiration time added to the payload
# jwt.encode() encodes the payload into a JWT
def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# function validates JWT token passed by the client
# jwt.decode() to decide the JWT checking the validity
# if valid it extracts username + password
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

# route used to create new user
# a user object is created and password is hashed using .hash()
# then added and saved to the db
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        surname = create_user_request.surname,
        role = create_user_request.role,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        is_active = True
    )

    db.add(create_user_model)
    db.commit()

# route used to handle user login + generates an access token
# takes form data authenticates it
# if authenticated creates JWT using the create_access_token
# returns JSON object with the type bearer
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    token = create_access_token(user.username, user.id, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}
