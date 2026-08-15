import { CalendarDays, MapPin, Sparkles, Star } from "lucide-react";
import { assetUrl, type Photo } from "../../api/client";

type MemoryTimelineProps = {
  photos: Photo[];
  selectedPhotoId: number | null;
  spotlightPhotoId: number | null;
  onSelectPhoto: (photoId: number) => void;
};

export function MemoryTimeline({
  photos,
  selectedPhotoId,
  spotlightPhotoId,
  onSelectPhoto
}: MemoryTimelineProps) {
  if (photos.length === 0) {
    return (
      <section className="timeline-view empty">
        <CalendarDays size={28} aria-hidden="true" />
        <div>
          <h2>No matching moments</h2>
          <p>Adjust search or filters to bring photos back into the timeline.</p>
        </div>
      </section>
    );
  }

  const groups = groupPhotos(photos);

  return (
    <section className="timeline-view">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Timeline</span>
          <h2>When it happened</h2>
        </div>
      </div>
      <div className="timeline-list">
        {groups.map((group) => (
          <section key={group.label} className="timeline-day">
            <h3>{group.label}</h3>
            {group.photos.map((photo) => (
              <button
                key={photo.id}
                type="button"
                className={`${photo.id === selectedPhotoId ? "selected" : ""} ${photo.id === spotlightPhotoId ? "spotlight" : ""}`}
                onClick={() => onSelectPhoto(photo.id)}
              >
                <img src={assetUrl(photo.image_url)} alt="" />
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
                      "Needs analysis"
                    )}
                  </small>
                  {photo.analysis?.uncertainty_notes.length ? (
                    <small>Uncertain evidence</small>
                  ) : null}
                  {photo.analysis?.user_note ? <small>{photo.analysis.user_note}</small> : null}
                </span>
                <span className="timeline-flags">
                  {photo.is_favorite ? <Star size={14} aria-hidden="true" /> : null}
                  <MapPin size={14} aria-hidden="true" />
                  {photo.latitude !== null && photo.longitude !== null ? "GPS" : "No GPS"}
                </span>
              </button>
            ))}
          </section>
        ))}
      </div>
    </section>
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
