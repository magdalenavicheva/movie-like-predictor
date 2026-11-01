from model.predictor import MoviePredictor

#load only once 
predictor = MoviePredictor()

MIN_RATINGS = predictor.min_ratings


def predict(ratings, movie_id):
    return predictor.predict(ratings, movie_id)