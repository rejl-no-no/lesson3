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


def check_for_redirect(response):
    if response.history:
        raise HTTPError()


def download_txt(parser_page, counter, download_response, folder="books/"):

    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(f'{folder}{counter}. {parser_page["title_name"]}.txt', "wb") as file:
        file.write(download_response.content)


def download_image(parser_page, folder="images/"):

    if not os.path.exists(folder):
        os.makedirs(folder)

    response = requests.get(parser_page["image_url"])
    response.raise_for_status()

    with open(f'{folder}{parser_page["image_name"]}', "wb") as file:
        file.write(response.content)


def parse_book_page(soup, url):

    body_text = soup.find("h1").text.split("::")
    title_name, author_name = body_text

    short_url_image = soup.find(class_="bookimage").find("img")["src"]
    image_url = urljoin(url, short_url_image)
    split_url_image = urllib.parse.urlsplit(image_url)
    path = split_url_image[-3]
    image_name = path.split("/")[-1]

    book_genre_tag = (
        soup.find(class_="ow_px_td").find("span", class_="d_book").find_all("a")
    )
    book_genres = [book_genre.text for book_genre in book_genre_tag]

    comments_tags = soup.find(class_="ow_px_td").find_all(class_="black")
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

    parser = argparse.ArgumentParser(description="Парсер онлайн библиотеки")
    parser.add_argument("--start_id", default = 1, type = int, help="С какой книги начинать скачивание")
    parser.add_argument("--end_id", default = 11, type = int, help="До какой книги качать")
    args = parser.parse_args()

    for counter in range(args.start_id, args.end_id):

        page_url = urljoin(url, f"/b{counter}/")
        download_payload = {"id":f"{counter}"}

        try:
            download_response = requests.get(urljoin(url,"txt.php"), params = download_payload)
            download_response.raise_for_status()


            url_response = requests.get(page_url)
            url_response.raise_for_status()


            soup = BeautifulSoup(url_response.text, "lxml")

            try:
                check_for_redirect(download_response)
                check_for_redirect(url_response)  
            except HTTPError:
                print(f"Книга №{counter} не найдена.")
            else:
                parser_page = parse_book_page(soup, url)
                download_txt(parser_page, counter, download_response)
                download_image(parser_page, folder="images/")

        except requests.exceptions.ConnectionError:
            print("Сбой сети!")
            time.sleep(2)
        except requests.exceptions.HTTPError:
            print("Страница не найднена!")
