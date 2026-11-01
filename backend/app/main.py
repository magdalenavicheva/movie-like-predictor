"""
The FastAPI backend.

Start it (from the backend folder):   uvicorn app.main:app --reload
Then open http://localhost:8000/docs to try every endpoint in the browser.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import movies, prediction
from .database import create_tables, engine, ratings_table

create_tables()

app = FastAPI(title="Movie Like Predictor")

# Allow the React frontend (http://localhost:5173) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Rating(BaseModel):
    movie_id: int
    liked: int          # 1 = like, 0 = dislike


class PredictRequest(BaseModel):
    ratings: list[Rating]
    movie_id: int
    user_id: str | None = None   # random id from the browser, to save the ratings of one user together


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/movies")
def get_movies(
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
    search: str = "",
    exclude: str = "",           # comma-separated movie ids, e.g. "155,27205"
):
    """One page of movies. The frontend asks for the next page with a higher offset."""
    exclude_ids = [int(x) for x in exclude.split(",") if x.strip().isdigit()]
    return movies.list_movies(offset, limit, search.strip(), exclude_ids)


@app.post("/api/predict")
def predict(request: PredictRequest):
    """Predict whether the user will like one movie, based on their ratings."""
    ratings = {r.movie_id: r.liked for r in request.ratings}

    if len(ratings) < prediction.MIN_RATINGS:
        raise HTTPException(400, f"Rate at least {prediction.MIN_RATINGS} movies first.")
    known = movies.existing_ids(list(ratings) + [request.movie_id])
    if request.movie_id not in known:
        raise HTTPException(404, "Movie not found.")
    if any(m not in known for m in ratings):
        raise HTTPException(400, "One of the rated movies doesn't exist.")

    # Save the user's ratings, so they can be used to retrain the model later.
    # The old ratings of this user are replaced, so asking several predictions doesn't save them twice.
    if request.user_id:
        with engine.begin() as conn:
            conn.execute(ratings_table.delete().where(ratings_table.c.user_id == request.user_id))
            conn.execute(ratings_table.insert(),
                         [{"user_id": request.user_id, "movie_id": m, "liked": l} for m, l in ratings.items()])

    return prediction.predict(ratings, request.movie_id)
