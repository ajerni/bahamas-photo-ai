import { Search, X } from "lucide-react";
import { PhotoMosaic } from "../components/photo/PhotoMosaic";
import { useTrip } from "../trip/TripProvider";
import { FILTER_OPTIONS, usePhotoFilters } from "../trip/usePhotoFilters";

export function PhotosPage() {
  const { trip, photos } = useTrip();
  const { query, setQuery, filters, visiblePhotos, isFiltered, toggleFilter, reset } =
    usePhotoFilters(photos);

  return (
    <div className="page photos-page">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Gallery</span>
          <h2>Every photo</h2>
        </div>
        <span className="count-pill">
          {visiblePhotos.length} of {photos.length}
        </span>
      </div>

      <div className="filter-bar">
        <label className="search-field">
          <Search size={15} aria-hidden="true" />
          <input
            type="search"
            value={query}
            placeholder="Search memories, places, moods…"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <div className="filter-chips">
          {FILTER_OPTIONS.map((option) => (
            <button
              key={option.key}
              type="button"
              className={filters[option.key] ? "active" : ""}
              onClick={() => toggleFilter(option.key)}
            >
              {option.label}
            </button>
          ))}
          {isFiltered ? (
            <button type="button" className="clear-filters" onClick={reset}>
              <X size={13} aria-hidden="true" />
              Clear
            </button>
          ) : null}
        </div>
      </div>

      <PhotoMosaic
        photos={visiblePhotos}
        coverPhotoId={trip?.cover_photo_id ?? null}
      />
    </div>
  );
}
