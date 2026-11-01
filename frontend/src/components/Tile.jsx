// One movie on the wall: the poster if there is one, otherwise the year and title as text.
// The wall uses the smaller w342 TMDB poster instead of w500, so pages load faster.
// state: "liked", "disliked" or "" (not rated)

export default function Tile({ movie, state, onClick }) {
  return (
    <button className={`tile ${state}`} onClick={onClick} title={movie.title}>
      {movie.poster_url ? (
        <img src={movie.poster_url.replace("/w500/", "/w342/")} alt={movie.title} loading="lazy" />
      ) : (
        <>
          <span className="tile-year">{movie.year}</span>
          <span className="tile-title">{movie.title}</span>
        </>
      )}
      {state === "liked" && <span className="dot" aria-label="liked" />}
    </button>
  );
}
