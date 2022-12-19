from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
import urllib.request
import argparse
import requests
import os
import errno
import time
import json


def check_for_redirect(response):
    if response.history:
        raise HTTPError()


def download_txt(title_name, book_id, download_response, dest_folder, folder_txt="books/"):

    os.makedirs(f'{dest_folder}{folder_txt}', exist_ok=True)

    with open(f'{dest_folder}{folder_txt}{book_id}. {title_name}.txt', "wb") as file:
        file.write(download_response.content)


def download_image(image_url, image_name, dest_folder, folder_img="images/"):

    os.makedirs(f'{dest_folder}{folder_img}', exist_ok=True)

    response = requests.get(image_url)
    response.raise_for_status()

    with open(f'{dest_folder}{folder_img}{image_name}', "wb") as file:
        file.write(response.content)


def parse_book_page(soup, page_url):

    body_text_selector = ('h1')    
    title_name, author_name =  soup.select_one(body_text_selector).text.split("::")


    image_url_selector = ('.bookimage img')
    short_image_url = soup.select_one(image_url_selector)['src']


    image_url = urljoin(page_url, short_image_url)
    splitted_image_url = urllib.parse.urlsplit(image_url)
    path = splitted_image_url[-3]
    image_name = path.split("/")[-1]

    book_genre_selector = "body .ow_px_td span.d_book a"
    book_genre_tag = soup.select(book_genre_selector)
    book_genres = [book_genre.text for book_genre in book_genre_tag]

    comments_selector = ".ow_px_td .black"
    comments_tags = soup.select(comments_selector)
    comments = [comment.text for comment in comments_tags]

    return {
        "title_name": sanitize_filename(title_name.strip()),
        "author_name":sanitize_filename(author_name.strip()),
        "image_name": image_name,
        "image_url": image_url,
        "book_genres": book_genres,
        "comments": comments,
    }


def create_json(books_specification):

    with open(f"{args.dest_folder}{args.json_path}page_content_json.json", "w", encoding='utf8') as file:
        json.dump(books_specification, file, ensure_ascii=False,  indent=2)


if __name__ == "__main__":

    url = "https://tululu.org/"
    books_specification = []

    parser = argparse.ArgumentParser(description="Парсер онлайн библиотеки")
    parser.add_argument("--start_id", default = 1, type = int, help="С какой книги начинать скачивание")
    parser.add_argument("--end_id", default = 702, type = int, help="До какой книги качать")
    parser.add_argument("--dest_folder", default = '', help="Путь к каталогу с резул. парсинга")
    parser.add_argument("--skip_imgs", action = 'store_true', help="Не скачивать изображения")
    parser.add_argument("--skip_txt", action = 'store_true', help="Не скачивать текст книги")
    parser.add_argument("--json_path", default = '', help="Путь к .json файлу")
    args = parser.parse_args()

    for count in range(args.start_id, args.end_id):

        fantastic_url = urljoin(url, f"l55/{count}/")

        try:
            url_response = requests.get(fantastic_url)
            url_response.raise_for_status()
            check_for_redirect(url_response)

        except requests.exceptions.ConnectionError:
            print("Сбой сети!")
            time.sleep(2)
        except requests.exceptions.HTTPError:
            print("Страница не найднена!")
        else:
            fantastic_soup = BeautifulSoup(url_response.text, "lxml")

            pages_id = fantastic_soup.select(".bookimage a")

            for page in pages_id:

                page_url = urljoin(url, page['href'])

                try:
                    url_response = requests.get(page_url)
                    url_response.raise_for_status()
                    check_for_redirect(url_response)

                    soup = BeautifulSoup(url_response.text, "lxml")

                    book_id_selector = '.r_comm input[name="bookid"]'
                    book_id = soup.select_one(book_id_selector)['value']

                    download_payload = {"id":f"{book_id}"}

                    download_response = requests.get(urljoin(url,"txt.php"), params = download_payload)
                    download_response.raise_for_status()
                    check_for_redirect(download_response)

                    page_content = parse_book_page(soup, page_url) 

                    if not args.skip_txt:
                        download_txt(page_content["title_name"], book_id, download_response, args.dest_folder)
                    if not args.skip_imgs:
                        download_image(page_content["image_url"], page_content["image_name"], args.dest_folder)

                    books_specification.append(page_content)

                except requests.exceptions.ConnectionError:
                    print("Сбой сети!")
                    time.sleep(2)
                except requests.exceptions.HTTPError:
                    print(f"Книга {book_id} не найднена!")

    create_json(books_specification)
