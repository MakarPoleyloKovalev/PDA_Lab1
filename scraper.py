import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "http://quotes.toscrape.com/page/{}/"


def scrape_page(page_num: int) -> list[dict]:
    url = BASE_URL.format(page_num)
    # Делаем запрос
    response = requests.get(url)
    if response.status_code != 200:
        return []

    # Передаем HTML в BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    quotes_data = []

    # Находим все блоки с цитатами
    for quote_block in soup.find_all('div', class_='quote'):
        # Извлекаем текст
        text = quote_block.find('span', class_='text').get_text(strip=True)

        # Извлекаем автора
        author_block = quote_block.find('small', class_='author')
        author = author_block.get_text(strip=True)

        # Извлекаем дату рождения автора (для этого нужно перейти на страницу автора)
        author_link = quote_block.find('a')['href']
        author_url = f"http://quotes.toscrape.com{author_link}"
        author_page = requests.get(author_url)
        author_soup = BeautifulSoup(author_page.text, 'html.parser')

        born_date_tag = author_soup.find('span', class_='author-born-date')
        born_date = born_date_tag.get_text(strip=True) if born_date_tag else None

        # Извлекаем теги
        tags = [tag.get_text(strip=True) for tag in quote_block.find_all('a', class_='tag')]

        quotes_data.append({
            'text': text,
            'author': author,
            'born_date': born_date,
            'tags': tags
        })

        time.sleep(0.1)  # Небольшая пауза, чтобы не нагружать сервер

    return quotes_data


def scrape_pages(num_pages: int) -> list[dict]:
    all_quotes = []
    for i in range(1, num_pages + 1):
        print(f"Парсинг страницы {i}...")
        all_quotes.extend(scrape_page(i))
    return all_quotes