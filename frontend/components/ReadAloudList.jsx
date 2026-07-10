"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchReadAloudFiltered } from "@/lib/api";
import { isAttempted } from "@/lib/attempts";

export default function ReadAloudList() {
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [order, setOrder] = useState("newest");
  const [complexity, setComplexity] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [showMoreFilters, setShowMoreFilters] = useState(false);

  const [data, setData] = useState({ items: [], total: 0, total_pages: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchReadAloudFiltered({ search, order, complexity, page, limit })
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [search, order, complexity, page, limit]);

  const visibleItems = data.items.filter((p) => {
    if (!statusFilter) return true;
    const attempted = isAttempted(p.id);
    return statusFilter === "attempted" ? attempted : !attempted;
  });

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  const handleClearFilters = () => {
    setSearchInput("");
    setSearch("");
    setOrder("newest");
    setComplexity("");
    setStatusFilter("");
    setPage(1);
  };

  return (
    <div className="qlist-card">
      <div className="qlist-header-row">
        <h4 className="qlist-title">Read Aloud</h4>
      </div>

      <form className="search-row" onSubmit={handleSearchSubmit}>
        <input
          className="search-input"
          placeholder="Search keywords"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <button type="submit" className="search-btn" aria-label="Search">🔍</button>
      </form>

      <div className="filters-row">
        <button className="more-filters-btn" onClick={() => setShowMoreFilters((s) => !s)}>
          {showMoreFilters ? "Hide Filters" : "More Filters"}
        </button>
        <button className="clear-link" onClick={handleClearFilters}>Clear</button>
      </div>

      {showMoreFilters && (
        <div className="filters-panel">
          <div className="filter-group">
            <label>Order by</label>
            <select value={order} onChange={(e) => { setOrder(e.target.value); setPage(1); }}>
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Complexity</label>
            <select value={complexity} onChange={(e) => { setComplexity(e.target.value); setPage(1); }}>
              <option value="">Select</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Difficult">Difficult</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Practice Status</label>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">Select</option>
              <option value="not_attempted">Not Attempted</option>
              <option value="attempted">Attempted</option>
            </select>
          </div>
        </div>
      )}

      {loading && <p className="loading-text">Loading passages...</p>}
      {error && <p className="loading-text">Error: {error}</p>}

      {!loading && !error && (
        <>
          <div className="qlist-mobile">
            {visibleItems.map((p) => (
              <div className="question-row" key={p.id}>
                <div className="rl-item-content">
                  <strong>#{p.id}</strong>{" "}
                  <span className={`complexity-badge ${p.complexity.toLowerCase()}`}>
                    {p.complexity}
                  </span>{" "}
                  <span className="passage-meta">{p.word_count} words</span>
                  <br />
                  <span className="rl-item-preview">{p.preview}</span>
                  <br />
                  {isAttempted(p.id) ? (
                    <span className="status-pill attempted">Attempted</span>
                  ) : (
                    <span className="status-pill not-attempted">Not Attempted</span>
                  )}
                </div>
                <Link className="view-btn" href={`/read-aloud/${p.id}`}>View</Link>
              </div>
            ))}
          </div>

          {visibleItems.length === 0 && (
            <p className="loading-text">No passages match your filters.</p>
          )}

          <div className="pagination-row">
            <div className="pagination-buttons">
              <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>←</button>
              {Array.from({ length: data.total_pages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  className={p === page ? "active-page" : ""}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
              <button disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)}>→</button>
            </div>
            <select value={limit} onChange={(e) => { setLimit(Number(e.target.value)); setPage(1); }}>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span>/Page</span>
          </div>
        </>
      )}
    </div>
  );
}
