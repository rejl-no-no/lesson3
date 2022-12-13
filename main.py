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


def download_txt(title_name, book_id, download_response, folder="books/"):

    os.makedirs(folder, exist_ok=True)

    with open(f'{folder}{book_id}. {title_name}.txt', "wb") as file:
        file.write(download_response.content)


def download_image(image_url, image_name, folder="images/"):

    os.makedirs(folder, exist_ok=True)

    response = requests.get(image_url)
    response.raise_for_status()

    with open(f'{folder}{image_name}', "wb") as file:
        file.write(response.content)


def parse_book_page(soup, page_url):

    body_text = soup.find("h1").text.split("::")
    title_name, author_name = body_text

    short_image_url = soup.find(class_="bookimage").find("img")["src"]

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


if __name__ == "__main__":

    url = "https://tululu.org/"
    json_content = []
    parser = argparse.ArgumentParser(description="Парсер онлайн библиотеки")
    parser.add_argument("--start_id", default = 1, type = int, help="С какой книги начинать скачивание")
    parser.add_argument("--end_id", default = 3, type = int, help="До какой книги качать")
    args = parser.parse_args()


    for count in range(1, 3):

        fantastic_url = urljoin(url, f"l55/{count}/")

        url_response = requests.get(fantastic_url)
        url_response.raise_for_status()
        fantastic_soup = BeautifulSoup(url_response.text, "lxml")

        pages_id = fantastic_soup.select(".bookimage")
        
        for page in pages_id:
            page_url = urljoin(url, page.find("a")["href"])

            try:
                url_response = requests.get(page_url)
                url_response.raise_for_status()

                soup = BeautifulSoup(url_response.text, "lxml")

                #book_id_selector = "attrs=bookid"
                #print(soup.select(book_id_selector))
                book_id = soup.find(attrs={"name": "bookid"})['value']
                download_payload = {"id":f"{book_id}"}

                download_response = requests.get(urljoin(url,"txt.php"), params = download_payload)
                download_response.raise_for_status()

                check_for_redirect(download_response)
                check_for_redirect(url_response)  

                page_content = parse_book_page(soup, page_url)

                books_description = json.dumps(json_content, ensure_ascii=False,  indent=2)

                with open("page_content_json.json", "w", encoding='utf8') as my_file:
                    my_file.write(books_description)

                with open("page_content_json.json", "w", encoding='utf8') as my_file:
                    json_content.append(page_content)
                    my_file.write(books_description)


                download_txt(page_content["title_name"], book_id, download_response)
                download_image(page_content["image_url"], page_content["image_name"])

            except requests.exceptions.ConnectionError:
                print("Сбой сети!")
                time.sleep(2)
            except requests.exceptions.HTTPError:
                print(f"Страница {book_id} не найднена!")
