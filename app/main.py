from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt

from datetime import timedelta, datetime
from .models import (
    User,
    Genre,
    Movie,
    MovieGenre
)


SECRET_KEY = "944ca420b8c316cabcd1885e9de6849f2350d1d29fa9d4f38fd8de33d4a31246"
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database
register_tortoise(
    app,
    db_url='sqlite://data/db.sqlite3',
    modules={'models': ['app.models']},
    generate_schemas=True,
    add_exception_handlers=True
)

UserPydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(
    User, exclude_readonly=True, name="UserIn")
GenrePydantic = pydantic_model_creator(Genre, name="Genre")
MoviePydantic = pydantic_model_creator(Movie, name="Movie")
MovieIn_Pydantic = pydantic_model_creator(
    Movie, exclude_readonly=True, name="MovieIn")
MovieGenrePydantic = pydantic_model_creator(MovieGenre, name="MovieGenre")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(username: str, password: str):
    if username is not None:
        user = await User.get_or_none(username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    if username is not None:
        user = await User.get_or_none(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.get('/')
async def ping():
    return {"ping": "pong"}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# @app.post('/register')
# async def user_register(user:UserIn_Pydantic):
#     user_obj = await User.create(**user.dict(exclude_unset=True)) # when inserting password to db, it should be hashed
#     return await UserPydantic.from_tortoise_orm(user_obj)

# @app.post("/user/")
# async def get_user(username: str):
#     if username is not None:
#         user = await User.get_or_none(username=username)
#         return user

# @app.get('/all_users')
# async def all_users():
#     user_dict =  await User.all().values()
#     return user_dict

# Movie endpoints


@app.get('/all_movies')
async def browse_movies():
    return await MoviePydantic.from_queryset(Movie.all())


@app.post('/add_movie')
async def add_movie(author_id: int, movie: MovieIn_Pydantic, auth: bool = Depends(get_current_active_user), genres: Optional[list] = None):
    movie_obj = await Movie.create(user_id=author_id, **movie.dict(exclude_unset=True))
    if len(genres) > 0:
        for genre in genres:
            await MovieGenre.create(movie_id=movie_obj.movie_id, genre_id=genre)
    return await MoviePydantic.from_tortoise_orm(movie_obj)


@app.put('/update_movie/{movie_id}')
async def update_movie(movie_id: int, movie: MovieIn_Pydantic, auth: bool = Depends(get_current_active_user)):
    await Movie.filter(movie_id=movie_id).update(**movie.dict(exclude_unset=True))
    return await MoviePydantic.from_queryset_single(Movie.get(movie_id=movie_id))


@app.delete('/delete_movie/{movie_id}')
async def delete_movie(movie_id: int, auth: bool = Depends(get_current_active_user)):
    status = await Movie.filter(movie_id=movie_id).delete()
    if not status:
        raise HTTPException(
            status_code=404, detail=f'Movie id {movie_id} "not found')
    return f'Movie id {movie_id} successfully deleted'


@app.get('/search')
async def search_movies(search_query: str):
    return await MoviePydantic.from_queryset(Movie.filter(movie_name__icontains=search_query))
