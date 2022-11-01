import requests
import os, errno


#def check_for_redirect(response):


def save_books():
    if not os.path.exists('books'):
        os.makedirs('books', exist_ok=True)

    os.chdir('books')

    counter = 1

    while counter <= 10:

        url = "https://tululu.org/txt.php?id=" + str(counter)

        response = requests.get(url)
        response.raise_for_status()

        if response.history == []:
            filename = 'id' + str(counter) + '.txt'

            with open(filename, 'wb') as file:
                file.write(response.content)
            

        counter+=1


#try:

#except:
#    raise HTTPError('Книга не существует')



if __name__ == "__main__":
    save_books()
