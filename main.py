from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
import urllib.request
import argparse
import requests
import os
import errno


def check_for_redirect(response):
    if response.history != []:
        raise HTTPError()


def download_txt(response_download, folder="books/"):

    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    with open(f'{folder}{counter}. {parser_data["title_name"]}.txt', "wb") as file:
        file.write(response_download.content)


def download_image(folder="images/"):

    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    response = requests.get(parser_data["image_url"])
    response.raise_for_status()

    with open(f'{folder}{parser_data["image_name"]}', "wb") as file:
        file.write(response.content)


def parse_book_page(soup):

    body_text = soup.find("h1").text.split("::")
    title_name = sanitize_filename(body_text[0].strip())
    author_name = sanitize_filename(body_text[1].strip())

    short_url_image = soup.find(class_="bookimage").find("img")["src"]
    image_url = urljoin(url, short_url_image)
    split_url_image = urllib.parse.urlsplit(image_url)
    path = split_url_image[-3]
    image_name = path.split("/")[-1]

    book_genres = []
    book_genre_tag = (
        soup.find(class_="ow_px_td").find("span", class_="d_book").find_all("a")
    )
    for book_genre in book_genre_tag:
        book_genres.append(book_genre.text)

    comments = []
    comments_tags = soup.find(class_="ow_px_td").find_all(class_="black")
    for comment in comments_tags:
        comments.append(comment.text)

    return {
        "title_name": title_name,
        "author_name": author_name,
        "image_name": image_name,
        "image_url": image_url,
        "book_genres": book_genres,
        "comments": comments,
    }


if __name__ == "__main__":
    url = "https://tululu.org/"

    parser = argparse.ArgumentParser(description="Парсер онлайн библиотеки")
    parser.add_argument("start_id", help="От какой книги начинать скачивание")
    parser.add_argument("end_id", help="До какой книги качать")
    args = parser.parse_args()

    for counter in range(int(args.start_id), int(args.end_id)):
        page_url = urljoin(url, f"/b{counter}")
        download_url = urljoin(url, f"txt.php?id={str(counter)}")

        response_download = requests.get(download_url)
        response_download.raise_for_status()

        response_url = requests.get(page_url)
        response_url.raise_for_status()

        soup = BeautifulSoup(response_url.text, "lxml")

        try:
            check_for_redirect(response_download)
        except HTTPError:
            print(f"Книга №{counter} не найдена.")
        else:
            parser_data = parse_book_page(soup)
            download_txt(response_download)
            download_image(folder="images/")