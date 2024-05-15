from fastapi import FastAPI, Depends, HTTPException, status
import psycopg2
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text

app = FastAPI(openapi_prefix='/posts')


SQL_DATABASE_URL = "postgresql://postgres:lakshyam@localhost/fastapisqlalchemy"

engine = create_engine(SQL_DATABASE_URL)

Base = declarative_base()

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, nullable=False, server_default="TRUE")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

Base.metadata.create_all(bind=engine)


class Posts(BaseModel):
    title: str
    content: str


class PostDetail(Posts):
    content:str
    # published:bool
    # created_at: datetime

    class Config:
        orm_mode = True


@app.get("/", response_model=list[PostDetail])
async def get_posts(db: Session = Depends(get_db)):
    get_posts = db.query(Post).all()
    if not get_posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No posts found")
    return get_posts


@app.get("/{id}", response_model=PostDetail)
async def get_post(id: int, db: Session = Depends(get_db)):
    get_post = db.query(Post).filter(Post.id == id).first()

    if not get_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} not found")
    return get_post


@app.post("/")
async def create_post(post: Posts, db: Session = Depends(get_db)):
    new_post = Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@app.put("/{id}")
async def update_posts(id: int, post: Posts, db: Session = Depends(get_db)):
    post_to_be_updated_query = db.query(Post).filter(Post.id == id)
    post_query = post_to_be_updated_query.first()

    if not post_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} not found")
    
    post_to_be_updated_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    return post_to_be_updated_query.first()


# tried to make the above code short,but below method will raise an error,because if we chain post_to_be_updated_query  variable value with first() method, Post object has no attribute 'update', so we have to follow the above process to be able to use update method 

# @app.put("/{id}")
# async def update_posts(id: int, post: Posts, db: Session = Depends(get_db)):
#     post_to_be_updated_query = db.query(Post).filter(Post.id == id).first()

#     if not post_to_be_updated_query:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} not found")
    
#     post_to_be_updated_query.update(post.model_dump(), synchronize_session=False)
#     db.commit()
#     return post_to_be_updated_query.first()


@app.delete("/{id}")
async def delete_post(id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id)
    post_del = post.first()

    if not post_del:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} not found")
    
    post.delete(synchronize_session=False)
    db.commit()
    return "Post Deleted Successfully"


@app.delete("/")
async def delete_all(db: Session = Depends(get_db)):
    '''All the posts can be deleted in one go'''
    post = db.query(Post)

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    post.delete(synchronize_session=False)
    db.commit()
    return "All posts deleted Successfully"