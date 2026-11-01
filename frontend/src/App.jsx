import { useState } from "react";
import { predict } from "./api.js";
import { MIN_RATINGS } from "./constants.js";
import Wall from "./components/Wall.jsx";
import Result from "./components/Result.jsx";

// Three screens:
//   "rate"   - the wall: click once to like, twice to dislike, three times to undo
//   "pick"   - the wall of movies you haven't rated: click one to get a prediction
//   "result" - the prediction for that movie
export default function App() {
  const [ratings, setRatings] = useState({});   // { movieId: 1 (like) or 0 (dislike) }
  const [screen, setScreen] = useState("rate");
  const [picked, setPicked] = useState(null);   // the movie on the result screen
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const count = Object.keys(ratings).length;

  // not rated -> like -> dislike -> not rated
  function cycle(movie) {
    setRatings((old) => {
      const next = { ...old };
      if (!(movie.id in next)) next[movie.id] = 1;
      else if (next[movie.id] === 1) next[movie.id] = 0;
      else delete next[movie.id];
      return next;
    });
  }

  function rateState(movie) {
    if (ratings[movie.id] === 1) return "liked";
    if (ratings[movie.id] === 0) return "disliked";
    return "";
  }

  async function choose(movie) {
    setPicked(movie);
    setScreen("result");
    setResult(null);
    setError("");
    setLoading(true);
    try {
      setResult(await predict(ratings, movie.id));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <span className="wordmark">LIKE / DISLIKE</span>

        {screen === "rate" && (
          <>
            <span className="quiet">Click once to like, twice to dislike</span>
            <div className="topbar-right">
              <span className="quiet">
                <strong>{count}</strong> / {MIN_RATINGS}
              </span>
              <button className="solid" disabled={count < MIN_RATINGS} onClick={() => setScreen("pick")}>
                NEXT
              </button>
            </div>
          </>
        )}

        {screen === "pick" && (
          <>
            <span className="quiet">Pick a movie you haven't seen</span>
            <button className="link" onClick={() => setScreen("rate")}>← RATE MORE</button>
          </>
        )}

        {screen === "result" && (
          <button className="link" onClick={() => setScreen("pick")}>← BACK TO THE WALL</button>
        )}
      </header>

      {screen === "rate" && <Wall tileState={rateState} onPick={cycle} />}
      {screen === "pick" && <Wall exclude={Object.keys(ratings)} tileState={() => ""} onPick={choose} />}
      {screen === "result" && picked && (
        <Result movie={picked} result={result} loading={loading} error={error} />
      )}
    </div>
  );
}
