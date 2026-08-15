import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Image as ImageIcon,
  Lock,
  Map,
  MapPin,
  Pencil,
  Pin,
  RefreshCw,
  Save,
  Sparkles,
  Star,
  Trash2,
  X
} from "lucide-react";
import { assetUrl, type Photo } from "../api/client";
import { useTrip } from "../trip/TripProvider";

type Draft = {
  user_memory_caption: string;
  user_scene_summary: string;
  user_mood: string;
  user_note: string;
};

export function PhotoDetailPage() {
  const { photoId } = useParams();
  const navigate = useNavigate();
  const { trip, photos, loading, savePhoto, removePhoto, reanalyzePhoto, saveTrip } =
    useTrip();

  const ordered = useMemo(
    () =>
      [...photos].sort(
        (a, b) => dateValue(a).getTime() - dateValue(b).getTime()
      ),
    [photos]
  );
  const index = ordered.findIndex((item) => item.id === Number(photoId));
  const photo = index === -1 ? null : ordered[index];

  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(draftFrom(photo));
    setError(null);
    setEditing(false);
  }, [photo?.id, photo?.analysis?.updated_at]);

  if (!photo) {
    return (
      <div className="page photo-detail-page">
        <section className="empty-state">
          <ImageIcon size={30} aria-hidden="true" />
          <h3>{loading ? "Opening the photo…" : "That photo is gone"}</h3>
          <p>
            <Link to="/photos">Back to the gallery</Link>
          </p>
        </section>
      </div>
    );
  }

  const analysis = photo.analysis;
  const isCover = trip?.cover_photo_id === photo.id;
  const previous = ordered[index - 1] ?? null;
  const next = ordered[index + 1] ?? null;

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this photo and its memory?")) {
      return;
    }
    await run(async () => {
      await removePhoto(photo!.id);
      navigate("/photos", { replace: true });
    });
  }

  return (
    <div className="page photo-detail-page">
      <div className="detail-topbar">
        <Link to="/photos" className="ghost-action">
          <ArrowLeft size={15} aria-hidden="true" />
          Gallery
        </Link>
        <div className="detail-stepper">
          <Link
            to={previous ? `/photos/${previous.id}` : "#"}
            className={`ghost-action ${previous ? "" : "disabled"}`}
            aria-disabled={previous ? undefined : true}
          >
            <ChevronLeft size={15} aria-hidden="true" />
            Previous
          </Link>
          <span>
            {index + 1} / {ordered.length}
          </span>
          <Link
            to={next ? `/photos/${next.id}` : "#"}
            className={`ghost-action ${next ? "" : "disabled"}`}
            aria-disabled={next ? undefined : true}
          >
            Next
            <ChevronRight size={15} aria-hidden="true" />
          </Link>
        </div>
      </div>

      <div className="detail-layout">
        <figure className="detail-stage">
          <img
            src={assetUrl(photo.image_url)}
            alt={analysis?.memory_caption || photo.filename}
          />
          <figcaption>
            <span>{photo.filename}</span>
            <span>{formatDate(photo.captured_at ?? photo.created_at)}</span>
            <span>
              <MapPin size={12} aria-hidden="true" />
              {photo.latitude !== null && photo.longitude !== null
                ? `${photo.latitude.toFixed(4)}, ${photo.longitude.toFixed(4)}`
                : "No GPS"}
            </span>
          </figcaption>
        </figure>

        <div className="detail-side">
          {error ? <p className="app-error">{error}</p> : null}

          {editing ? (
            <>
              <form
                className="detail-editor"
                onSubmit={(event) => {
                  event.preventDefault();
                  void run(async () => {
                    await savePhoto(photo.id, toPayload(draft));
                    setEditing(false);
                  });
                }}
              >
                <span className="soft-kicker">Your words</span>
                <label>
                  Caption
                  <input
                    value={draft.user_memory_caption}
                    placeholder={analysis?.memory_caption || photo.filename}
                    onChange={(event) =>
                      setDraft({ ...draft, user_memory_caption: event.target.value })
                    }
                  />
                </label>
                <label>
                  What happened
                  <textarea
                    rows={4}
                    value={draft.user_scene_summary}
                    placeholder={analysis?.scene_summary || "Describe the scene"}
                    onChange={(event) =>
                      setDraft({ ...draft, user_scene_summary: event.target.value })
                    }
                  />
                </label>
                <label>
                  Mood
                  <input
                    value={draft.user_mood}
                    placeholder={analysis?.mood || "How it felt"}
                    onChange={(event) =>
                      setDraft({ ...draft, user_mood: event.target.value })
                    }
                  />
                </label>
                <label>
                  Private note
                  <textarea
                    rows={3}
                    value={draft.user_note}
                    placeholder="Only for you"
                    onChange={(event) =>
                      setDraft({ ...draft, user_note: event.target.value })
                    }
                  />
                </label>
                <div className="detail-editor-buttons">
                  <button type="submit" className="primary-action" disabled={busy}>
                    <Save size={15} aria-hidden="true" />
                    Save
                  </button>
                  <button
                    type="button"
                    className="ghost-action"
                    disabled={busy}
                    onClick={() => {
                      setDraft(draftFrom(photo));
                      setEditing(false);
                    }}
                  >
                    <X size={15} aria-hidden="true" />
                    Cancel
                  </button>
                </div>
              </form>

              <div className="detail-actions">
                <button
                  type="button"
                  className={`chip-action ${isCover ? "active" : ""}`}
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      saveTrip({ cover_photo_id: isCover ? null : photo.id })
                    )
                  }
                >
                  <Pin size={15} aria-hidden="true" />
                  {isCover ? "Cover" : "Make cover"}
                </button>
                <button
                  type="button"
                  className="chip-action"
                  disabled={busy}
                  onClick={() => void run(() => reanalyzePhoto(photo.id))}
                >
                  <RefreshCw size={15} aria-hidden="true" />
                  Read again
                </button>
                <button
                  type="button"
                  className="chip-action danger"
                  disabled={busy}
                  onClick={() => void handleDelete()}
                >
                  <Trash2 size={15} aria-hidden="true" />
                  Delete
                </button>
              </div>
            </>
          ) : (
            <>
              <article className="detail-memory">
                {analysis ? (
                  <>
                    <h1>
                      {analysis.user_memory_caption ||
                        analysis.memory_caption ||
                        photo.filename}
                    </h1>
                    <p>{analysis.user_scene_summary || analysis.scene_summary}</p>
                    <div className="memory-facets">
                      <Facet
                        label="Mood"
                        value={analysis.user_mood || analysis.mood}
                      />
                      <Facet label="Place" value={analysis.place_type} />
                    </div>
                    {analysis.user_note ? (
                      <aside className="memory-note">
                        <span className="soft-kicker">
                          <Lock size={12} aria-hidden="true" />
                          Private note
                        </span>
                        <p>{analysis.user_note}</p>
                      </aside>
                    ) : null}
                    <div className="memory-tags">
                      <TagList label="Doing" values={analysis.visible_activities} />
                      <TagList label="Objects" values={analysis.visible_objects} />
                      <TagList label="Details" values={analysis.sensory_details} />
                    </div>
                  </>
                ) : (
                  <div className="detail-model-read pending">
                    <Sparkles size={16} aria-hidden="true" />
                    <p>No memory yet. It arrives on its own once the photo is read.</p>
                  </div>
                )}
              </article>

              <div className="detail-actions">
                <button
                  type="button"
                  className={`chip-action ${photo.is_favorite ? "active" : ""}`}
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      savePhoto(photo.id, { is_favorite: !photo.is_favorite })
                    )
                  }
                >
                  <Star
                    size={15}
                    aria-hidden="true"
                    fill={photo.is_favorite ? "currentColor" : "none"}
                  />
                  Favourite
                </button>
                {photo.latitude !== null && photo.longitude !== null ? (
                  <Link
                    to={`/map?focus=${photo.id}`}
                    className="chip-action"
                  >
                    <Map size={15} aria-hidden="true" />
                    Show on map
                  </Link>
                ) : null}
                <button
                  type="button"
                  className="chip-action"
                  onClick={() => setEditing(true)}
                >
                  <Pencil size={15} aria-hidden="true" />
                  Edit
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Facet({ label, value }: { label: string; value: string | null }) {
  if (!value) {
    return null;
  }
  return (
    <div className="facet">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function TagList({ label, values }: { label: string; values: string[] }) {
  const cleaned = values.filter(Boolean);
  if (cleaned.length === 0) {
    return null;
  }
  return (
    <div className="tag-line">
      <span>{label}</span>
      <div className="tag-cloud">
        {cleaned.map((value) => (
          <span key={value}>{value}</span>
        ))}
      </div>
    </div>
  );
}

const emptyDraft: Draft = {
  user_memory_caption: "",
  user_scene_summary: "",
  user_mood: "",
  user_note: ""
};

function draftFrom(photo: Photo | null): Draft {
  const analysis = photo?.analysis;
  return {
    user_memory_caption: analysis?.user_memory_caption ?? "",
    user_scene_summary: analysis?.user_scene_summary ?? "",
    user_mood: analysis?.user_mood ?? "",
    user_note: analysis?.user_note ?? ""
  };
}

function toPayload(draft: Draft) {
  return {
    user_memory_caption: draft.user_memory_caption.trim() || null,
    user_scene_summary: draft.user_scene_summary.trim() || null,
    user_mood: draft.user_mood.trim() || null,
    user_note: draft.user_note.trim() || null
  };
}

function dateValue(photo: Photo): Date {
  return new Date(photo.captured_at ?? photo.created_at);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
