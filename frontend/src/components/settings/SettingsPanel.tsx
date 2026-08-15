import { useEffect, useState } from "react";
import { Download, FileArchive, Trash2 } from "lucide-react";
import {
  assetUrl,
  exportTripMarkdown,
  exportTripZip,
  type Photo
} from "../../api/client";
import { useTrip } from "../../trip/TripProvider";

export function SettingsPanel() {
  const { trip, photos, saveTrip, removeAllPhotos, clearMemories } = useTrip();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setTitle(trip?.title ?? "");
    setDescription(trip?.description ?? "");
  }, [trip?.title, trip?.description]);

  const dirty = trip !== null && (title !== trip.title || description !== (trip.description ?? ""));

  async function run(label: string, action: () => Promise<void>) {
    setBusy(true);
    setStatus(null);
    try {
      await action();
      setStatus(label);
    } catch (cause) {
      setStatus((cause as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings-panel">
      <section className="settings-section">
        <h3>Trip</h3>
        <label>
          <span>Title</span>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Bahamas 2026"
          />
        </label>
        <label>
          <span>Subtitle</span>
          <input
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Buernis on tour"
          />
        </label>
        <button
          type="button"
          className="primary-action"
          disabled={!dirty || busy || !title.trim()}
          onClick={() =>
            run("Trip saved", () =>
              saveTrip({ title: title.trim(), description: description.trim() || null })
            )
          }
        >
          Save trip details
        </button>
      </section>

      <CoverPicker photos={photos} coverPhotoId={trip?.cover_photo_id ?? null} />

      <section className="settings-section">
        <h3>Export</h3>
        <p className="settings-hint">Take the whole memory with you.</p>
        <div className="settings-row">
          <button
            type="button"
            className="secondary-action"
            disabled={!trip || busy}
            onClick={() =>
              run("Markdown downloaded", async () => {
                const file = await exportTripMarkdown(trip!.id);
                download(new Blob([file.content], { type: "text/markdown" }), file.filename);
              })
            }
          >
            <Download size={15} aria-hidden="true" />
            Markdown
          </button>
          <button
            type="button"
            className="secondary-action"
            disabled={!trip || busy}
            onClick={() =>
              run("ZIP downloaded", async () => {
                const file = await exportTripZip(trip!.id);
                download(file.blob, file.filename);
              })
            }
          >
            <FileArchive size={15} aria-hidden="true" />
            ZIP dossier
          </button>
        </div>
      </section>

      <section className="settings-section danger">
        <h3>Danger zone</h3>
        <p className="settings-hint">
          These cannot be undone. The trip itself always stays.
        </p>
        <button
          type="button"
          className="danger-action"
          disabled={busy || photos.length === 0}
          onClick={() => {
            if (window.confirm("Clear every AI memory? The photos stay.")) {
              void run("Memories cleared", clearMemories);
            }
          }}
        >
          <Trash2 size={15} aria-hidden="true" />
          Clear all memories
        </button>
        <button
          type="button"
          className="danger-action"
          disabled={busy || photos.length === 0}
          onClick={() => {
            if (window.confirm(`Delete all ${photos.length} photos and their memories?`)) {
              void run("All photos deleted", removeAllPhotos);
            }
          }}
        >
          <Trash2 size={15} aria-hidden="true" />
          Delete all photos
        </button>
      </section>

      {status ? <p className="settings-status">{status}</p> : null}
    </div>
  );
}

function CoverPicker({
  photos,
  coverPhotoId
}: {
  photos: Photo[];
  coverPhotoId: number | null;
}) {
  const { saveTrip } = useTrip();

  if (photos.length === 0) {
    return null;
  }

  return (
    <section className="settings-section">
      <h3>Cover photo</h3>
      <div className="cover-picker">
        {photos.map((photo) => (
          <button
            key={photo.id}
            type="button"
            className={photo.id === coverPhotoId ? "active" : ""}
            title={photo.analysis?.memory_caption || photo.filename}
            onClick={() =>
              void saveTrip({
                cover_photo_id: photo.id === coverPhotoId ? null : photo.id
              })
            }
          >
            <img src={assetUrl(photo.image_url)} alt="" />
          </button>
        ))}
      </div>
    </section>
  );
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
