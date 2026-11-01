"""
predictor.py - predicts whether a user will like a movie, and explains why.

Used by the app (FastAPI). It needs these files in the same folder:
- movies.csv            (from get_movies.py)
- movie_scaler.joblib   (from data.ipynb, section 4.2)
- model.joblib          (from final_model.ipynb, section 5)
- model_info.json       (from final_model.ipynb, section 5)

How to use it:
    from predictor import MoviePredictor

    predictor = MoviePredictor()
    ratings = {157336: 1, 27205: 1, 19995: 0, ...}   # movie_id: 1 = like, 0 = dislike (at least 15)
    result = predictor.predict(ratings, movie_id=155)
    print(result["chance"], result["prediction"], result["reasons"])
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

GENRES = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Family",
          "Fantasy", "History", "Horror", "Music", "Mystery", "Romance",
          "Science Fiction", "Thriller", "War", "Western"]


class MoviePredictor:

    def __init__(self, folder=None):
        """Load the model, the model info, the scaler and the movies once, when the app starts."""
        folder = Path(folder) if folder else Path(__file__).parent

        self.model = joblib.load(folder / "model.joblib")
        with open(folder / "model_info.json") as f:
            self.info = json.load(f)
        self.features = self.info["features"]
        self.threshold = self.info["threshold"]
        self.min_ratings = self.info["min_profile_ratings"]
        self.coefficients = dict(zip(self.features, self.model.coef_[0]))

        # The movies, with the same genre columns and scaling as in data.ipynb
        self.movies = pd.read_csv(folder / "movies.csv").set_index("id")
        scaler = joblib.load(folder / "movie_scaler.joblib")
        genre_table = self.movies["genres"].str.get_dummies(sep="|").reindex(columns=GENRES, fill_value=0)
        scaled = scaler.transform(self.movies[["year", "runtime", "rating"]])
        self.movie_table = genre_table.assign(year_s=scaled[:, 0], runtime_s=scaled[:, 1], rating_s=scaled[:, 2])

    # ------------------------------------------------------------------
    # Step 1: the user's profile, from their ratings
    # ------------------------------------------------------------------
    def build_profile(self, ratings):
        """
        ratings = {movie_id: 1 or 0}. Returns like_share and like_<genre>,
        calculated the same way as in the notebooks.
        """
        if len(ratings) < self.min_ratings:
            raise ValueError(f"A user needs at least {self.min_ratings} ratings, got {len(ratings)}.")
        unknown = [m for m in ratings if m not in self.movie_table.index]
        if unknown:
            raise ValueError(f"Unknown movie ids: {unknown}")

        rated = self.movie_table.loc[list(ratings)]
        liked = np.array(list(ratings.values()))

        like_share = liked.mean()
        like_genres = {}
        for g in GENRES:
            n_rated = rated[g].sum()
            # same rule as the notebooks: a genre the user didn't rate gets their like_share
            like_genres[g] = (rated[g].values * liked).sum() / n_rated if n_rated > 0 else like_share

        return {"like_share": like_share, "like_genres": like_genres}

    # ------------------------------------------------------------------
    # Step 2: the 5 features for one movie
    # ------------------------------------------------------------------
    def movie_features(self, profile, movie_id):
        """The 5 model features for this user and this movie, in the order the model expects."""
        movie = self.movie_table.loc[movie_id]
        movie_genres = [g for g in GENRES if movie[g] == 1]
        genre_match = np.mean([profile["like_genres"][g] for g in movie_genres])

        values = {
            "rating_s": movie["rating_s"],
            "year_s": movie["year_s"],
            "runtime_s": movie["runtime_s"],
            "like_share": profile["like_share"],
            "genre_match": genre_match,
        }
        return {f: float(values[f]) for f in self.features}

    # ------------------------------------------------------------------
    # Step 3: predict
    # ------------------------------------------------------------------
    def predict(self, ratings, movie_id, n_reasons=3):
        """Chance that the user likes the movie, the prediction, and the main reasons."""
        profile = self.build_profile(ratings)
        values = self.movie_features(profile, movie_id)
        row = pd.DataFrame([values], columns=self.features)
        chance = float(self.model.predict_proba(row)[0, 1])

        return {
            "movie_id": int(movie_id),
            "title": self.movies.loc[movie_id, "title"],
            "chance": round(chance, 3),
            "prediction": "like" if chance >= self.threshold else "dislike",
            "reasons": self.explain(values, movie_id, profile, n_reasons),
        }

    # ------------------------------------------------------------------
    # Explanation: why this prediction?
    # ------------------------------------------------------------------
    def explain(self, values, movie_id, profile, n_reasons=3):
        """
        For logistic regression, each feature pushes the prediction up or down by
        coefficient x (value - average value). The average is the average in the training data,
        so a push of 0 means 'this feature is just like for an average rating'.
        Returns the features with the biggest push, as readable sentences.
        """
        means = self.info["feature_means"]
        movie = self.movies.loc[movie_id]
        movie_genres = [g for g in GENRES if self.movie_table.loc[movie_id, g] == 1]
        liked_genres = [g for g in movie_genres if profile["like_genres"][g] >= profile["like_share"]]
        disliked_genres = [g for g in movie_genres if profile["like_genres"][g] < profile["like_share"]]

        reasons = []
        for f in self.features:
            push = self.coefficients[f] * (values[f] - means[f])
            above = values[f] >= means[f]
            if f == "rating_s":
                text = (f"It is rated higher than most movies (TMDB {movie['rating']:.1f})" if above
                        else f"It is rated lower than most movies (TMDB {movie['rating']:.1f})")
            elif f == "year_s":
                text = (f"It is a newer movie ({movie['year']})" if above
                        else f"It is an older movie ({movie['year']})")
            elif f == "runtime_s":
                text = (f"It is a long movie ({movie['runtime']} min)" if above
                        else f"It is a short movie ({movie['runtime']} min)")
            elif f == "like_share":
                text = (f"You like most movies you rate ({values[f]:.0%})" if above
                        else f"You are picky: you like {values[f]:.0%} of the movies you rate")
            else:  # genre_match
                text = (f"You usually like its genres ({', '.join(liked_genres or movie_genres)})" if above
                        else f"You often don't like its genres ({', '.join(disliked_genres or movie_genres)})")
            reasons.append({"feature": f, "text": text,
                            "effect": "like" if push > 0 else "dislike", "push": round(float(push), 3)})

        reasons.sort(key=lambda r: abs(r["push"]), reverse=True)
        return [r for r in reasons if abs(r["push"]) >= 0.05][:n_reasons]
