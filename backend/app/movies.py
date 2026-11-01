"""
The movies, read from the PostgreSQL database.

The frontend never gets all 500 movies at once: it asks for one page at a time
(for example 24 movies), and asks for the next page when the user clicks "Show more".
"""

from sqlalchemy import func, select

from .database import engine, movies_table as m

LIST_COLUMNS = [m.c.id, m.c.title, m.c.year, m.c.runtime, m.c.rating, m.c.genres, m.c.poster_url]


def list_movies(offset=0, limit=24, search="", exclude=()):
    """
    One page of movies, most voted first (so users see movies they probably know).
    search  = only titles that contain this text (not case-sensitive)
    exclude = movie ids to leave out (the movies the user already rated)
    Returns {"items": [...], "total": number of movies that match}.
    """
    conditions = []
    if search:
        conditions.append(m.c.title.ilike(f"%{search}%"))
    if exclude:
        conditions.append(m.c.id.not_in(list(exclude)))

    page = (select(*LIST_COLUMNS).where(*conditions)
            .order_by(m.c.vote_count.desc(), m.c.id).offset(offset).limit(limit))
    count = select(func.count()).select_from(m).where(*conditions)

    with engine.connect() as conn:
        items = [dict(row._mapping) for row in conn.execute(page)]
        total = conn.execute(count).scalar()
    return {"items": items, "total": total}


def get_movie(movie_id):
    """One movie as a dictionary, or None if the id doesn't exist."""
    with engine.connect() as conn:
        row = conn.execute(select(m).where(m.c.id == movie_id)).first()
    return dict(row._mapping) if row else None


def existing_ids(movie_ids):
    """Which of these movie ids exist in the database."""
    with engine.connect() as conn:
        rows = conn.execute(select(m.c.id).where(m.c.id.in_(list(movie_ids))))
        return {row.id for row in rows}
