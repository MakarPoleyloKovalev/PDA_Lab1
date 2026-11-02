import pandas as pd
from sqlalchemy import create_engine, text, func, select
from sqlalchemy.orm import Session
from models import Quote, Author, Tag, QuoteTag

SQLITE_URI = "sqlite:///lab_quotes.db"


def run_analytics():
    engine = create_engine(SQLITE_URI)

    print("\n" + "=" * 60)
    print("1. Топ-5 авторов по количеству цитат")
    print("=" * 60)

    # --- Способ 1: SQLAlchemy ---
    with Session(engine) as session:
        query1 = (
            select(Author.name, func.count(Quote.id).label("quotes_count"))
            .join(Quote, Quote.author_id == Author.id)
            .group_by(Author.name)
            .order_by(func.count(Quote.id).desc())
            .limit(5)
        )
        res1_sql = session.execute(query1).all()
        print("SQLAlchemy:")
        for row in res1_sql:
            print(f"  {row.name}: {row.quotes_count} цитат")

    # --- Способ 2: Pandas ---
    df_authors = pd.read_sql(select(Author), engine)
    df_quotes = pd.read_sql(select(Quote), engine)
    merged_1 = df_quotes.merge(df_authors, left_on='author_id', right_on='id')
    res1_pd = merged_1.groupby('name').size().reset_index(name='quotes_count')
    res1_pd = res1_pd.sort_values(by='quotes_count', ascending=False).head(5)
    print("\nPandas:")
    print(res1_pd.to_string(index=False))

    print("\n" + "=" * 60)
    print("2. Самые популярные теги (Топ-5)")
    print("=" * 60)

    # --- Способ 1: SQLAlchemy ---
    with Session(engine) as session:
        query2 = (
            select(Tag.name, func.count(QuoteTag.quote_id).label("usage_count"))
            .join(QuoteTag, QuoteTag.tag_id == Tag.id)
            .group_by(Tag.name)
            .order_by(func.count(QuoteTag.quote_id).desc())
            .limit(5)
        )
        res2_sql = session.execute(query2).all()
        print("SQLAlchemy:")
        for row in res2_sql:
            print(f"  {row.name}: {row.usage_count} раз")

    # --- Способ 2: Pandas ---
    df_tags = pd.read_sql(select(Tag), engine)
    df_qt = pd.read_sql(select(QuoteTag), engine)
    merged_2 = df_qt.merge(df_tags, left_on='tag_id', right_on='id')
    res2_pd = merged_2.groupby('name').size().reset_index(name='usage_count')
    res2_pd = res2_pd.sort_values(by='usage_count', ascending=False).head(5)
    print("\nPandas:")
    print(res2_pd.to_string(index=False))

    print("\n" + "=" * 60)
    print("3. Количество цитат у авторов, родившихся до 1950 года")
    print("=" * 60)

    # --- Способ 1: SQLAlchemy ---
    with Session(engine) as session:
        # Ищем года, которые начинаются с 18.. или 19.. (до 1950)
        query3 = (
            select(Author.name, func.count(Quote.id).label("count"))
            .join(Quote)
            .where(func.substr(Author.born_date, 1, 4) < "1950")
            .group_by(Author.name)
            .order_by(func.count(Quote.id).desc())
        )
        res3_sql = session.execute(query3).all()
        print("SQLAlchemy:")
        if not res3_sql:
            print("  Нет данных.")
        for row in res3_sql:
            print(f"  {row.name}: {row.count}")

    # --- Способ 2: Pandas ---
    df_authors_copy = df_authors.copy()
    df_authors_copy['year'] = pd.to_numeric(df_authors_copy['born_date'].str[-4:], errors='coerce')
    df_authors_old = df_authors_copy[df_authors_copy['year'] < 1950]

    merged_3 = df_quotes.merge(df_authors_old, left_on='author_id', right_on='id')
    res3_pd = merged_3.groupby('name').size().reset_index(name='count').sort_values('count', ascending=False)

    print("\nPandas:")
    if res3_pd.empty:
        print("  Нет данных.")
    else:
        print(res3_pd.to_string(index=False))

    print("\n" + "=" * 60)
    print("4. Средняя длина текста цитаты (в символах)")
    print("=" * 60)

    # --- Способ 1: SQLAlchemy (через чистый SQL) ---
    with engine.connect() as conn:
        query4 = text("SELECT AVG(LENGTH(text)) as avg_len FROM quotes")
        res4_sql = conn.execute(query4).scalar()
        print(f"SQLAlchemy (Raw SQL): {res4_sql:.1f} символов")

    # --- Способ 2: Pandas ---
    df_quotes['text_length'] = df_quotes['text'].apply(len)
    res4_pd = df_quotes['text_length'].mean()
    print(f"Pandas: {res4_pd:.1f} символов")

    print("\n" + "=" * 60)
    print("5. Авторы, у которых есть хотя бы одна цитата с тегом 'love'")
    print("=" * 60)

    # --- Способ 1: SQLAlchemy ---
    with Session(engine) as session:
        query5 = (
            select(Author.name)
            .join(Quote, Quote.author_id == Author.id)
            .join(QuoteTag, QuoteTag.quote_id == Quote.id)
            .join(Tag, Tag.id == QuoteTag.tag_id)
            .where(Tag.name == 'love')
            .distinct()
        )
        res5_sql = session.execute(query5).all()
        print("SQLAlchemy:")
        for row in res5_sql:
            print(f"  - {row.name}")

    # --- Способ 2: Pandas ---
    # Переименовываем колонки в df_tags, чтобы избежать конфликта имен
    df_tags_renamed = df_tags.rename(columns={'id': 'tag_id_ref', 'name': 'tag_name'})

    # Делаем слияние по шагам, чтобы четко отслеживать названия колонок
    step1 = df_quotes.merge(df_authors, left_on='author_id', right_on='id')  # id_x = id цитаты
    step2 = step1.merge(df_qt, left_on='id_x', right_on='quote_id')  # Берем id_x
    step3 = step2.merge(df_tags_renamed, left_on='tag_id', right_on='tag_id_ref')

    # Фильтруем и берем уникальные имена авторов
    res5_pd = step3[step3['tag_name'] == 'love']['name'].unique()

    print("\nPandas:")
    for name in res5_pd:
        print(f"  - {name}")


if __name__ == "__main__":
    run_analytics()