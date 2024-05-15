from fastapi import FastAPI, status, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from pydantic import BaseModel

app = FastAPI()

while True:
    try:
        conn = psycopg2.connect(host = 'localhost',database = 'api_practise', user = "postgres", password = 'lakshyam', cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        if conn:
            print("Connected to Database Successfully")
            break
    except Exception as error:
        print(f"Error: {error}")
        time.sleep(3)


class Post(BaseModel):
    title: str
    content: str
    published: bool = True 

class PostDetail(Post):
    id: int


@app.get("/posts", response_model=list[PostDetail], tags=["Read"])
async def get_posts():
    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    return posts


@app.get("/posts/{id}", response_model=PostDetail, tags=["Read"])
async def get_post(id: int):
    cursor.execute("SELECT * FROM posts WHERE id = %s",(str(id),))
    post = cursor.fetchone()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} not found")
    return post


@app.post("/create_post", response_model=PostDetail, status_code=status.HTTP_201_CREATED, tags=["Create"])
async def create_post(post: Post):
    cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s,%s,%s) RETURNING * """, (post.title, post.content, post.published))

    post = cursor.fetchone()
    conn.commit()
    return post


@app.put("/posts/{id}", response_model=PostDetail, tags=["Update"])
async def update_post(post: Post, id: int):
    cursor.execute("""UPDATE posts SET title=%s, content=%s, published=%s WHERE id = %s RETURNING * """,(post.title, post.content, post.published, str(id)))
    updated_post = cursor.fetchone()
    if not updated_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} not found")
    conn.commit()
    return updated_post


@app.delete("/posts/{id}", response_model=PostDetail, tags=["Delete"])
async def delete_post(id: int):
    cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING * """, (str(id),))
    deleted_post = cursor.fetchone()
    if not deleted_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} not found")
    conn.commit()
    return deleted_post


@app.delete("/posts", response_model=list[PostDetail], tags=["Delete"])
async def delete_all_posts():
    cursor.execute("""DELETE FROM posts RETURNING * """)
    deleted_posts = cursor.fetchall()
    if not deleted_posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No posts created yet")
    conn.commit()
    return deleted_posts