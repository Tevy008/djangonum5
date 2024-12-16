import argparse
import json
import os
from time import sleep
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, unquote, urlsplit


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def get_category_book_urls(start_page, end_page):
    all_full_urls = []
    all_numbers_text = []
    for number_page in range(start_page, end_page):
        try:
            tululu_url = f'https://tululu.org/l55/{number_page}'
            response = requests.get(tululu_url)
            response.raise_for_status()
            check_for_redirect(response)
            soup = BeautifulSoup(response.text, 'lxml')
            books_selector = 'table.d_book'
            books_urls = soup.select(books_selector)
            for book_url in books_urls:
                url = book_url.find('a')['href']
                book_full_url = urljoin(tululu_url, url)
                split_url = urlsplit(url).path.split('/')[1]
                all_full_urls.append(book_full_url)
                all_numbers_text.append(split_url)
        except requests.exceptions.HTTPError:
            print('книга не найдена')
        except requests.exceptions.ConnectionError:
            print("Повторное подключение к серверу")
            sleep(20)
    return all_full_urls, all_numbers_text



def download_txt(url, number, filename, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    params = {'id' : number}
    response = requests.get(url, params=params)
    response.raise_for_status() 
    check_for_redirect(response)
    filepath = os.path.join(folder, f'{sanitize_filename(filename)}.txt')
    with open(filepath, 'wb') as file:
        file.write(response.content)


def download_image(image_url, folder='images/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(image_url)
    response.raise_for_status() 
    check_for_redirect(response)
    image_name = urlsplit(image_url).path.split('/')[-1]
    filepath = os.path.join(folder, image_name)
    with open(unquote(filepath), 'wb') as file:
        file.write(response.content)


def parse_book_page(response, template_url):
    soup = BeautifulSoup(response.text, 'lxml')
    book_image_selector = 'div.bookimage img'
    book_image_url = soup.select_one(book_image_selector)['src']
    full_image_url = urljoin(template_url, book_image_url)
    title = soup.select_one('h1').text
    book_title, book_author = title.split(' :: ')
    book_comments_selector = 'div.texts span.black'
    book_comments = soup.select(book_comments_selector)
    comments = [comment.text for comment in book_comments]
    books_genres_select = 'span.d_book a'
    books_genres = soup.select(books_genres_select)
    books_genres = [genre.text for genre in books_genres]                                                                               
    book_parameters = {
        "title": book_title.strip(),
        "author": book_author.strip(),
        "image_url": full_image_url,
        "genre": books_genres,
        "comments": comments
    }
    return book_parameters

def main():
    parser = argparse.ArgumentParser(
        description= "Проект скачивает книги и соответствующие им картинки,\
                     а также собирает информацию о книге"
    )
    parser.add_argument(
        "--start_page",
        type=int,
        help="Стартовая страница для скачивания",
        default=1
    )
    parser.add_argument(
        "--end_page", 
        type=int,
        help="Конечная страница для скачивания", 
        default=10
        )
    parser.add_argument(
        "--dest_folder",
        help="Путь к каталогу с результатами парсинга",
        default="Folder"
    )
    parser.add_argument(
        "--skip_imgs",
        action="store_true",
        help="Не скачивать картинки"
    )
    parser.add_argument(
        "--skip_txt",
        action="store_true",
        help="Не скачивать книги"
    )
    parser.add_argument(
        "--json_path",
        help="Путь к JSON файлу с информацией о книгах",
        default="Folder"
    )
    args = parser.parse_args()
    imgs_dir = f"./{args.dest_folder}/images"
    books_dir = f"./{args.dest_folder}/books"

    os.makedirs(imgs_dir, exist_ok=True)
    os.makedirs(books_dir, exist_ok=True)

    all_books_parameters = []
    book_urls, book_numbers = get_category_book_urls(args.start_page, args.end_page)
    for book_url, number_book in zip(book_urls, book_numbers):
        try:
            response = requests.get(book_url)
            response.raise_for_status() 
            check_for_redirect(response)
            book_parameters = parse_book_page(response, book_url)
            if not args.skip_imgs:
                download_image(book_parameters['image_url'], folder=imgs_dir)
            book_title = book_parameters['title']
            filename = f'{book_title.strip()}'
            url_txt_book = f'https://tululu.org/txt.php'
            if not args.skip_txt:
                download_txt(url_txt_book, number_book[1:], filename, folder=books_dir)
            all_books_parameters.append(book_parameters)
        except requests.exceptions.HTTPError:
            print('книга не найдена')
        except requests.exceptions.ConnectionError:
            print("Повторное подключение к серверу")
            sleep(20)
    with open("data.json", "w", encoding='utf8') as file:
        json.dump(all_books_parameters, file, ensure_ascii=False)
   

if __name__=='__main__':
    main()