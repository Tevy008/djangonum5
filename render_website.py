import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from more_itertools import chunked
import math

    

with open("data.json", "r", encoding="UTF-8") as file:
    file_contents = file.read()
library_books = json.loads(file_contents)

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)

template = env.get_template('template.html')

books_pages = list(chunked(library_books, 10))
total_pages = len(books_pages)
os.makedirs("Pages", exist_ok=True)

for number,book_page in enumerate(books_pages):

    rendered_page = template.render(
        book_parameters = chunked(book_page,2),
        current_page=number + 1,
        all_books_pages = total_pages
    )
    with open(f'Pages/index{number+1}.html', 'w', encoding="UTF-8") as file:
        file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
server.serve_forever()
