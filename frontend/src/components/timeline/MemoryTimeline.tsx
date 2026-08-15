import { Link } from "react-router-dom";
import { CalendarDays, MapPin, Sparkles, Star } from "lucide-react";
import { assetUrl, type Photo } from "../../api/client";

export function MemoryTimeline({ photos }: { photos: Photo[] }) {
  if (photos.length === 0) {
    return (
      <section className="timeline-view empty">
        <CalendarDays size={28} aria-hidden="true" />
        <div>
          <h2>Nothing on the timeline</h2>
          <p>Add photos from the menu and they land here in order.</p>
        </div>
      </section>
    );
  }

  const groups = groupPhotos(photos);

  return (
    <div className="timeline-list">
      {groups.map((group) => (
        <section key={group.label} className="timeline-day">
          <h3>{group.label}</h3>
          {group.photos.map((photo) => (
            <Link key={photo.id} to={`/photos/${photo.id}`}>
              <img src={assetUrl(photo.image_url)} alt="" loading="lazy" />
              <span>
                <em>{formatTime(photo.captured_at ?? photo.created_at)}</em>
                <strong>{photo.analysis?.memory_caption || photo.filename}</strong>
                <small>
                  {photo.analysis ? (
                    <>
                      <Sparkles size={12} aria-hidden="true" />
                      {photo.analysis.user_mood || photo.analysis.mood || "Remembered"}
                    </>
                  ) : (
                    "Still remembering"
                  )}
                </small>
              </span>
              <span className="timeline-flags">
                {photo.is_favorite ? <Star size={14} aria-hidden="true" /> : null}
                <MapPin size={14} aria-hidden="true" />
                {photo.latitude !== null && photo.longitude !== null ? "GPS" : "No GPS"}
              </span>
            </Link>
          ))}
        </section>
      ))}
    </div>
  );
}

function groupPhotos(photos: Photo[]) {
  const groups = new Map<string, Photo[]>();
  [...photos]
    .sort((a, b) => dateValue(a).getTime() - dateValue(b).getTime())
    .forEach((photo) => {
      const label = formatDay(dateValue(photo).toISOString());
      groups.set(label, [...(groups.get(label) ?? []), photo]);
    });
  return [...groups.entries()].map(([label, groupedPhotos]) => ({
    label,
    photos: groupedPhotos
  }));
}

function dateValue(photo: Photo): Date {
  return new Date(photo.captured_at ?? photo.created_at);
}

function formatDay(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(value));
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
