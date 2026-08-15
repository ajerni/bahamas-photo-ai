import { Link } from "react-router-dom";
import { Images, Pin, Sparkles, Star } from "lucide-react";
import { assetUrl, type Photo } from "../../api/client";

type PhotoMosaicProps = {
  photos: Photo[];
  coverPhotoId: number | null;
};

export function PhotoMosaic({ photos, coverPhotoId }: PhotoMosaicProps) {
  if (photos.length === 0) {
    return (
      <section className="photos-view empty">
        <Images size={28} aria-hidden="true" />
        <div>
          <h2>No photos here</h2>
          <p>Add photos from the menu, or clear the filters above.</p>
        </div>
      </section>
    );
  }

  return (
    <div className="photo-mosaic-grid">
      {photos.map((photo) => (
        <article
          key={photo.id}
          className={photo.is_favorite ? "tall" : ""}
        >
          <Link to={`/photos/${photo.id}`} className="mosaic-photo-button">
            <img
              src={assetUrl(photo.image_url)}
              alt={photo.analysis?.memory_caption || photo.filename}
              loading="lazy"
            />
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
          </Link>
          <MosaicBadges
            isFavorite={photo.is_favorite}
            isCover={coverPhotoId === photo.id}
          />
        </article>
      ))}
    </div>
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
