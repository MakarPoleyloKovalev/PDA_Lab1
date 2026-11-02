from scraper import scrape_pages
from database import Database


def main():
    # Парсим первые 3 страницы (около 30 цитат)
    print("Начинаем сбор данных...")
    scraped_data = scrape_pages(3)
    print(f"Собрано цитат: {len(scraped_data)}")

    # Сохраняем в базу
    db = Database()
    result = db.save_quotes(scraped_data)

    print(f"\nУспешно добавлено: {result['added']}")
    print(f"Пропущено дубликатов: {result['skipped']}")


if __name__ == "__main__":
    main()