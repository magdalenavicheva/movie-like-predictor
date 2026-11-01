import { useEffect, useRef, useState } from "react";
import { getMovies } from "../api.js";
import Tile from "./Tile.jsx";

const PAGE_SIZE = 24;

// The poster wall. It loads movies from the backend one page at a time:
// the first 24 when it opens, the next 24 each time "Show more" is clicked.
// exclude   = movie ids to leave out (on the pick screen: the movies already rated)
// tileState = function: how a tile looks ("liked", "disliked" or "")
// onPick    = function: what happens when a tile is clicked
export default function Wall({ exclude = [], tileState, onPick }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");        // the search text, 300 ms after the user stops typing
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const requestId = useRef(0);                   // so an old, slow answer can't overwrite a newer one
  const excludeKey = exclude.join(",");

  // Wait until the user stops typing before searching.
  useEffect(() => {
    const timer = setTimeout(() => setQuery(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search]);

  async function load(offset) {
    const id = ++requestId.current;
    setLoading(true);
    setError("");
    try {
      const page = await getMovies({ offset, limit: PAGE_SIZE, search: query, exclude });
      if (id !== requestId.current) return;
      setItems((old) => (offset === 0 ? page.items : [...old, ...page.items]));
      setTotal(page.total);
    } catch (e) {
      if (id === requestId.current) setError(e.message);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }

  // First page: when the wall opens, and again when the search changes.
  useEffect(() => {
    load(0);
  }, [query, excludeKey]);

  return (
    <main className="wall">
      <input
        className="search"
        placeholder="Search a movie"
        aria-label="Search a movie"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {error && <p className="error">{error}</p>}

      <div className="grid">
        {items.map((movie) => (
          <Tile key={movie.id} movie={movie} state={tileState(movie)} onClick={() => onPick(movie)} />
        ))}
      </div>

      {!loading && !error && items.length === 0 && <p className="quiet">No movies found.</p>}

      {items.length < total && (
        <button className="outline more" disabled={loading} onClick={() => load(items.length)}>
          {loading ? "LOADING…" : `SHOW MORE  (${items.length} / ${total})`}
        </button>
      )}
    </main>
  );
}
