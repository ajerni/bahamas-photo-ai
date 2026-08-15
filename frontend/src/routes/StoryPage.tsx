import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Images, Pencil, Sparkles, X } from "lucide-react";
import { assetUrl, type MemorableMoment, type Photo } from "../api/client";
import { useTrip } from "../trip/TripProvider";

export function StoryPage() {
  const { trip, photos, memory, storyStale } = useTrip();

  const remembered = photos.filter((photo) => photo.analysis !== null).length;
  const mapped = photos.filter(
    (photo) => photo.latitude !== null && photo.longitude !== null
  ).length;

  return (
    <div className="page story-page">
      <TripHero coverPhoto={findCover(photos, trip?.cover_photo_id ?? null)} />

      <div className="stat-strip">
        <Stat value={photos.length} label="Photos" />
        <Stat value={mapped} label="Places" />
        <Stat value={remembered} label="Memories" />
      </div>

      {memory ? (
        <>
          {storyStale ? (
            <p className="stale-note">
              <Sparkles size={14} aria-hidden="true" />
              A photo changed since this story was written.
            </p>
          ) : null}

          <NarrativeSection
            narrative={memory.user_narrative_summary || memory.narrative_summary}
            isEdited={Boolean(memory.user_narrative_summary)}
          />

          <MomentsSection moments={memory.memorable_moments} photos={photos} />

          <ThemesSection
            themes={memory.recurring_themes}
            interests={memory.inferred_interests}
          />
        </>
      ) : (
        <EmptyStory hasPhotos={photos.length > 0} />
      )}
    </div>
  );
}

function TripHero({ coverPhoto }: { coverPhoto: Photo | null }) {
  const { trip } = useTrip();

  return (
    <section className={`trip-hero ${coverPhoto ? "has-cover" : ""}`}>
      {coverPhoto ? (
        <img src={assetUrl(coverPhoto.image_url)} alt="" className="trip-hero-image" />
      ) : null}
      <div className="trip-hero-body">
        <span className="soft-kicker">Trip memory</span>
        <h2>{trip?.title}</h2>
        {trip?.description ? <p>{trip.description}</p> : null}
      </div>
    </section>
  );
}

function NarrativeSection({
  narrative,
  isEdited
}: {
  narrative: string;
  isEdited: boolean;
}) {
  const { saveMemory } = useTrip();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(narrative);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setDraft(narrative);
  }, [narrative]);

  async function save() {
    setSaving(true);
    try {
      await saveMemory({ user_narrative_summary: draft.trim() || null });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="story-section narrative">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">The story</span>
          <h3>How it felt</h3>
        </div>
        {editing ? null : (
          <button type="button" className="ghost-action" onClick={() => setEditing(true)}>
            <Pencil size={14} aria-hidden="true" />
            Edit
          </button>
        )}
      </div>

      {editing ? (
        <div className="inline-editor">
          <textarea
            value={draft}
            rows={8}
            onChange={(event) => setDraft(event.target.value)}
            autoFocus
          />
          <div className="inline-editor-actions">
            <button type="button" className="primary-action" disabled={saving} onClick={save}>
              <Check size={15} aria-hidden="true" />
              Save
            </button>
            <button
              type="button"
              className="ghost-action"
              onClick={() => {
                setDraft(narrative);
                setEditing(false);
              }}
            >
              <X size={15} aria-hidden="true" />
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className="narrative-body">{narrative}</p>
          {isEdited ? <span className="edited-flag">Edited by you</span> : null}
        </>
      )}
    </section>
  );
}

function MomentsSection({
  moments,
  photos
}: {
  moments: MemorableMoment[];
  photos: Photo[];
}) {
  if (moments.length === 0) {
    return null;
  }

  return (
    <section className="story-section">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Highlights</span>
          <h3>Moments worth keeping</h3>
        </div>
      </div>
      <div className="moment-rail">
        {moments.map((moment) => {
          const photo = photos.find((item) =>
            moment.evidence_photo_ids.includes(item.id)
          );
          return (
            <article key={moment.title} className="moment-card">
              {photo ? (
                <Link to={`/photos/${photo.id}`}>
                  <img src={assetUrl(photo.image_url)} alt="" />
                </Link>
              ) : null}
              <div>
                <strong>{moment.title}</strong>
                <p>{moment.description}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function ThemesSection({
  themes,
  interests
}: {
  themes: string[];
  interests: string[];
}) {
  const tags = [...new Set([...themes, ...interests])];
  if (tags.length === 0) {
    return null;
  }

  return (
    <section className="story-section">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Threads</span>
          <h3>What kept coming back</h3>
        </div>
      </div>
      <div className="tag-cloud">
        {tags.map((tag) => (
          <span key={tag}>{tag}</span>
        ))}
      </div>
    </section>
  );
}

function EmptyStory({ hasPhotos }: { hasPhotos: boolean }) {
  return (
    <section className="empty-state">
      <Images size={30} aria-hidden="true" />
      <h3>{hasPhotos ? "Memories are still forming" : "This trip is empty"}</h3>
      <p>
        {hasPhotos
          ? "Your photos are being read right now. The story appears once every photo has a memory."
          : "Add photos from the menu and the story writes itself."}
      </p>
    </section>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function findCover(photos: Photo[], coverPhotoId: number | null): Photo | null {
  if (photos.length === 0) {
    return null;
  }
  return (
    photos.find((photo) => photo.id === coverPhotoId) ??
    photos.find((photo) => photo.is_favorite) ??
    photos[0]
  );
}
