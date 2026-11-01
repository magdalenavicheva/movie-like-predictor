"""
The connection to the PostgreSQL database, and the two tables.
"""

import os

from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, MetaData, String, Table, Text,
                        create_engine, func)


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/movie_app")
engine = create_engine(DATABASE_URL)
metadata = MetaData()

movies_table = Table(
    "movies", metadata,
    Column("id", Integer, primary_key=True),          # the TMDB id
    Column("title", String, nullable=False),
    Column("year", Integer),
    Column("runtime", Integer),
    Column("rating", Float),
    Column("vote_count", Integer),
    Column("genres", String),
    Column("poster_url", String),
    Column("overview", Text),
)

ratings_table = Table(
    "ratings", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False),        # the random id from the browser
    Column("movie_id", Integer, ForeignKey("movies.id"), nullable=False),
    Column("liked", Integer, nullable=False),         # 1 = like, 0 = dislike
    Column("created_at", DateTime, server_default=func.now()),
)


def create_tables():
    """Create the tables if they don't exist yet."""
    metadata.create_all(engine)
