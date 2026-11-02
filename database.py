import hashlib
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, Author, Tag, Quote, QuoteTag

SQLITE_URI = "sqlite:///lab_quotes.db"


class Database:
    def __init__(self, uri=SQLITE_URI):
        # Создаем подключение
        self.engine = create_engine(uri)
        # Создаем таблицы (если их нет)
        Base.metadata.create_all(self.engine)

    def save_quotes(self, scraped_quotes: list[dict]):
        added = 0
        skipped = 0

        # Открываем сессию
        with Session(self.engine) as session:
            # Все изменения сохранятся одной транзакцией
            with session.begin():
                for item in scraped_quotes:
                    # Генерируем хеш текста для проверки на дубликаты
                    q_hash = hashlib.md5(item['text'].encode('utf-8')).hexdigest()

                    # Проверяем, есть ли уже такая цитата
                    existing = session.scalar(select(Quote).where(Quote.quote_hash == q_hash))
                    if existing:
                        skipped += 1
                        continue

                    # 1. Сохраняем автора (если его еще нет)
                    author = session.scalar(select(Author).where(Author.name == item['author']))
                    if not author:
                        author = Author(name=item['author'], born_date=item['born_date'])
                        session.add(author)
                        session.flush()  # flush нужен, чтобы получить author.id из базы

                    # 2. Сохраняем цитату
                    quote = Quote(text=item['text'], author_id=author.id, quote_hash=q_hash)
                    session.add(quote)
                    session.flush()

                    # 3. Сохраняем теги и связи
                    for tag_name in item['tags']:
                        tag = session.scalar(select(Tag).where(Tag.name == tag_name))
                        if not tag:
                            tag = Tag(name=tag_name)
                            session.add(tag)
                            session.flush()

                        # Связываем цитату и тег
                        session.add(QuoteTag(quote_id=quote.id, tag_id=tag.id))

                    added += 1
        return {"added": added, "skipped": skipped}