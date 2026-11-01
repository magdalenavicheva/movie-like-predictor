"""
Puts your 500 TMDB movies from data/movies.csv into the database.
Run it ONCE, from the backend folder:   python load_movies.py
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import func, select

from app.database import create_tables, engine, movies_table

CSV = Path(__file__).parent / "data" / "movies.csv"
COLUMNS = ["id", "title", "year", "runtime", "rating", "vote_count", "genres", "poster_url", "overview"]

if not CSV.exists():
    sys.exit("data/movies.csv not found. Copy your movies.csv (from get_movies.py) into backend/data/ first.")

create_tables()

with engine.begin() as conn:
    already = conn.execute(select(func.count()).select_from(movies_table)).scalar()
    if already > 0:
        print(f"The movies table already has {already} movies. Nothing to do.")
    else:
        movies = pd.read_csv(CSV)
        rows = movies[COLUMNS].astype(object).where(movies[COLUMNS].notna(), None).to_dict(orient="records")
        conn.execute(movies_table.insert(), rows)
        print(f"Added {len(rows)} movies to the database.")
