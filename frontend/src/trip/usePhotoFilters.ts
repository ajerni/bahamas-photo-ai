import { useMemo, useState } from "react";
import type { Photo } from "../api/client";

export type FilterKey = "favorites" | "noGps";

export const FILTER_OPTIONS: Array<{ key: FilterKey; label: string }> = [
  { key: "favorites", label: "Favourite" },
  { key: "noGps", label: "No GPS" }
];

const EMPTY_FILTERS: Record<FilterKey, boolean> = {
  favorites: false,
  noGps: false
};

export function usePhotoFilters(photos: Photo[]) {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<Record<FilterKey, boolean>>(EMPTY_FILTERS);

  const visiblePhotos = useMemo(
    () => filterPhotos(photos, query, filters),
    [photos, query, filters]
  );

  const activeCount = Object.values(filters).filter(Boolean).length;

  return {
    query,
    setQuery,
    filters,
    visiblePhotos,
    isFiltered: query.trim() !== "" || activeCount > 0,
    toggleFilter(key: FilterKey) {
      setFilters((current) => ({ ...current, [key]: !current[key] }));
    },
    reset() {
      setQuery("");
      setFilters(EMPTY_FILTERS);
    }
  };
}

function filterPhotos(
  photos: Photo[],
  query: string,
  filters: Record<FilterKey, boolean>
): Photo[] {
  const normalizedQuery = query.trim().toLowerCase();

  return photos.filter((photo) => {
    const mapped = photo.latitude !== null && photo.longitude !== null;

    if (filters.favorites && !photo.is_favorite) {
      return false;
    }
    if (filters.noGps && mapped) {
      return false;
    }
    return normalizedQuery === "" || photoText(photo).includes(normalizedQuery);
  });
}

function photoText(photo: Photo): string {
  const analysis = photo.analysis;
  return [
    photo.filename,
    analysis?.memory_caption,
    analysis?.scene_summary,
    analysis?.place_type,
    analysis?.user_mood,
    analysis?.user_note,
    ...(analysis?.visible_activities ?? []),
    ...(analysis?.visible_objects ?? []),
    ...(analysis?.sensory_details ?? [])
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}
