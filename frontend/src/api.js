// All calls to the FastAPI backend. Vite sends /api/... on to http://localhost:8000.

// One page of movies from the database.
// exclude = ids of movies to leave out (the ones the user already rated)
export async function getMovies({ offset = 0, limit = 24, search = "", exclude = [] } = {}) {
  const params = new URLSearchParams({ offset, limit, search, exclude: exclude.join(",") });
  const response = await fetch(`/api/movies?${params}`);
  if (!response.ok) throw new Error("Could not load the movies. Is the backend running?");
  return response.json(); // { items: [...], total: 500 }
}

// A random id per browser, so the backend can save the ratings of one user together.
function getUserId() {
  let id = localStorage.getItem("userId");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("userId", id);
  }
  return id;
}

// ratings = { movieId: 1 or 0, ... }
export async function predict(ratings, movieId) {
  const response = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ratings: Object.entries(ratings).map(([id, liked]) => ({ movie_id: Number(id), liked })),
      movie_id: movieId,
      user_id: getUserId(),
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Prediction failed.");
  return data;
}
