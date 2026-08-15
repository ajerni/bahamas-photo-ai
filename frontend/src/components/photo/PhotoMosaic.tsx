import { Clock3, Images, MapPin, Pin, Sparkles, Star } from "lucide-react";
import { assetUrl, type Photo } from "../../api/client";

type PhotoMosaicProps = {
  photos: Photo[];
  selectedPhotoId: number | null;
  spotlightPhotoId: number | null;
  coverPhotoId: number | null;
  isRefining: boolean;
  onSelectPhoto: (photoId: number) => void;
  onUpdatePhoto: (
    photoId: number,
    payload: { is_favorite?: boolean }
  ) => void | Promise<void>;
};

export function PhotoMosaic({
  photos,
  selectedPhotoId,
  spotlightPhotoId,
  coverPhotoId,
  isRefining,
  onSelectPhoto,
  onUpdatePhoto
}: PhotoMosaicProps) {
  if (photos.length === 0) {
    return (
      <section className="photos-view empty">
        <Images size={28} aria-hidden="true" />
        <div>
          <h2>No photos yet</h2>
          <p>Import travel photos to begin building the trip gallery.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="photos-view">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Gallery</span>
          <h2>Photos from this trip</h2>
        </div>
      </div>
      <div className="photo-mosaic-grid">
        {photos.map((photo, index) => (
          <article
            key={photo.id}
            className={`${photo.id === selectedPhotoId ? "selected" : ""} ${photo.id === spotlightPhotoId ? "spotlight" : ""} ${index % 5 === 0 ? "large" : ""}`}
          >
            <button
              type="button"
              className="mosaic-photo-button"
              onClick={() => onSelectPhoto(photo.id)}
            >
              <img src={assetUrl(photo.image_url)} alt={photo.analysis?.memory_caption || photo.filename} />
              <span>
                <strong>{photo.analysis?.memory_caption || photo.filename}</strong>
                <em>
                  {photo.analysis ? (
                    <>
                      <Sparkles size={12} aria-hidden="true" />
                      Remembered
                    </>
                  ) : (
                    "Waiting for memory"
                  )}
                </em>
              </span>
            </button>
            {isRefining ? (
              <button
                type="button"
                className={`mosaic-favorite ${photo.is_favorite ? "active" : ""}`}
                onClick={() => onUpdatePhoto(photo.id, { is_favorite: !photo.is_favorite })}
                title={photo.is_favorite ? "Remove from kept moments" : "Keep this moment"}
              >
                <Star size={15} aria-hidden="true" />
              </button>
            ) : (
              <MosaicBadges
                isFavorite={photo.is_favorite}
                isCover={coverPhotoId === photo.id}
              />
            )}
          </article>
        ))}
      </div>

      <div className="photo-sequence">
        <div className="section-heading compact">
          <div>
            <span className="soft-kicker">Sequence</span>
            <h2>When it happened</h2>
          </div>
        </div>
        <div className="sequence-list">
          {photos.map((photo) => (
            <button
              key={photo.id}
              type="button"
              className={photo.id === selectedPhotoId ? "selected" : ""}
              onClick={() => onSelectPhoto(photo.id)}
            >
              <img src={assetUrl(photo.image_url)} alt="" />
              <span>
                <em>
                  <Clock3 size={12} aria-hidden="true" />
                  {formatDate(photo.captured_at ?? photo.created_at)}
                </em>
                <strong>{photo.analysis?.memory_caption || photo.filename}</strong>
                <small>
                  <MapPin size={12} aria-hidden="true" />
                  {photo.latitude !== null && photo.longitude !== null ? "Mapped" : "No GPS"}
                </small>
              </span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function MosaicBadges({
  isFavorite,
  isCover
}: {
  isFavorite: boolean;
  isCover: boolean;
}) {
  if (!isFavorite && !isCover) {
    return null;
  }

  return (
    <div className="mosaic-badges" aria-label="Photo status">
      {isFavorite ? <Star size={14} aria-hidden="true" /> : null}
      {isCover ? <Pin size={14} aria-hidden="true" /> : null}
    </div>
  );
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
