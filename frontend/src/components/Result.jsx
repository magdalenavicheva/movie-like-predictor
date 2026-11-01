// The prediction, split in two: the movie on the left, the chance and the reasons on the right.

export default function Result({ movie, result, loading, error }) {
  const genres = movie.genres.split("|").join(" · ").toUpperCase();

  return (
    <main className="result">
      <div className="result-movie">
        <span className="small-caps">
          {movie.year} · {genres} · {movie.runtime} MIN
        </span>
        <h2 className="result-title">{movie.title}</h2>
      </div>

      <div className="result-answer">
        {loading && <p className="quiet">Predicting…</p>}
        {error && <p className="error">{error}</p>}
        {result && !loading && (
          <>
            {result.demo && <p className="demo">Demo prediction: the real model isn't connected yet.</p>}
            <div className="chance">
              <span className="chance-number">{Math.round(result.chance * 100)}</span>
              <span className="small-caps">% CHANCE YOU'LL LIKE IT</span>
              <span className="verdict">{result.prediction === "like" ? "Probably yes." : "Probably not."}</span>
            </div>
            <ul className="reasons">
              {result.reasons.map((r) => (
                <li key={r.feature} className={r.effect}>
                  <span className="sign">{r.effect === "like" ? "+" : "−"}</span>
                  <span>{r.text}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </main>
  );
}
