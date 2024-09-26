from typing import Optional

from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from pygments.lexer import default

app = FastAPI()

class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(self, id, title, author, description, rating, published_date):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


class BookRequest(BaseModel):
    id: Optional[int] = Field(description="ID is not needed on create", default=None)
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=-1, lt=6)
    published_date: str

    model_config = {
        "json_schema_extra": {
            "example": {
                'title': "A new book",
                'author': "name of author",
                'description': "A new description of the book",
                'rating': 5,
                'published_date': "06-01-2002"
            }
        }
    }


BOOKS = [
    Book(1, "Computer Science Pro", "Muhsin", "Best book", 5, "20-01-1948"),
    Book(2, "Be Fast with FastAPI", "Muhsin", "Great book", 5, "17-08-2020"),
    Book(3, "MAster Endpoints", "Muhsin", "Awesome book", 5, "06-05-1888"),
    Book(4, "HP1", "Author 1", "Nice", 2, "03-04-1928"),
    Book(5, "HP2", "Author 2", "Nice", 3, "28-07-2008"),
    Book(6, "HP3", "Author 3", "Nice", 1, "12-12-2015")
]

# returns all the books in the list BOOKS
@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_all_books():
    return BOOKS

# path parameter
@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def read_book(book_id: int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book

    raise HTTPException(status_code=404, detail='Item not found!')

# assignment solution
@app.get("/books/{published_date}", status_code=status.HTTP_200_OK)
async def read_book_by_rating(published_date: str):
    books_to_return = []
    for book in BOOKS:
        if book.published_date == published_date:
            BOOKS.append(book)

    return books_to_return

# query parameter
@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            BOOKS.append(book)

    return books_to_return

# assignment solution
@app.get("/books/publish", status_code=status.HTTP_200_OK)
async def read_book_by_rating(published_date: str):
    books_to_return = []
    for book in BOOKS:
        if book.published_date == published_date:
            BOOKS.append(book)

    return books_to_return

# creates new book
@app.post("/create-book", status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest):
    # converts the request to book object
    new_book = Book(**book_request.model_dump())
    BOOKS.append(find_book_id(new_book))

# auto increment for book_id
def find_book_id(book: Book):
    if len(BOOKS) > 0:
        book.id = BOOKS[-1].id + 1
    else:
        book.id = 1

    return book

@app.put("/books/update_book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book: BookRequest):
    book_changed = False
    new_book = Book(**book.model_dump())
    for i in range(len(BOOKS)):
        if BOOKS[i].id  == new_book.id:
            BOOKS[i] = new_book
            book_changed = True

    if not book_changed:
        raise HTTPException(status_code=404, detail='Item not found!')

@app.delete("/books/{book_id", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int = Path(gt=0)):
    book_deleted = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            book_deleted = True
            break

    if not book_deleted:
        raise HTTPException(status_code=404, detail='Item not found!')

"""
Add a new field to Book and BookRequest called published_date: int (for example, published_date: int = 2012). So, this book as published on the year of 2012.
Enhance each Book to now have a published_date
Then create a new GET Request method to filter by published_date
"""