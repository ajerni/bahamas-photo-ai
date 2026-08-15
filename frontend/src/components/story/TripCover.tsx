import {
  Download,
  ImagePlus,
  MapPin,
  MoreHorizontal,
  Pin,
  RotateCcw,
  Sparkles
} from "lucide-react";
import {
  assetUrl,
  type AnalysisJob,
  type Photo,
  type Trip
} from "../../api/client";
import {
  jobDetail,
  jobPercent,
  jobRemaining,
  jobStage,
  jobStepCount
} from "./jobStatus";

type TripCoverProps = {
  trip: Trip | null;
  coverPhoto: Photo | null;
  photos: Photo[];
  selectedPhoto: Photo | null;
  photoCount: number;
  locatedCount: number;
  analyzedCount: number;
  missingAnalysisCount: number;
  backendReady: boolean;
  modelReady: boolean;
  analyzeDisabled: boolean;
  job: AnalysisJob | null;
  onAnalyze: (mode: "all" | "missing") => void;
  onCancelJob: () => void;
  onRetryJob: () => void;
  onSetCover: (photoId: number) => void;
  onExportMarkdown: () => void;
  onExportZip: () => void;
};

export function TripCover({
  trip,
  coverPhoto,
  photos,
  selectedPhoto,
  photoCount,
  locatedCount,
  analyzedCount,
  missingAnalysisCount,
  backendReady,
  modelReady,
  analyzeDisabled,
  job,
  onAnalyze,
  onCancelJob,
  onRetryJob,
  onSetCover,
  onExportMarkdown,
  onExportZip
}: TripCoverProps) {
  const title = trip?.title ?? "Start a private trip";
  const description =
    trip?.description ||
    (photoCount > 0
      ? "Your photos are ready. Develop them into a private trip memory."
      : "Import travel photos to begin building a local memory map.");
  const running = job && (job.status === "queued" || job.status === "running" || job.status === "cancel_requested");
  const primaryMode = analyzedCount > 0 && missingAnalysisCount > 0 ? "missing" : "all";
  const buttonLabel =
    photoCount === 0
      ? "Add photos first"
      : running
        ? "Developing..."
        : !backendReady
          ? "Backend offline"
          : !modelReady
            ? "Model not ready"
          : analyzedCount > 0 && missingAnalysisCount > 0
            ? "Develop new photos"
        : analyzedCount > 0
          ? "Develop again"
          : "Develop memories";

  return (
    <section className={`trip-cover ${coverPhoto ? "has-photo" : "empty"}`}>
      {coverPhoto ? (
        <img
          key={coverPhoto.id}
          className="trip-cover-image"
          src={assetUrl(coverPhoto.image_url)}
          alt={coverPhoto.analysis?.memory_caption || coverPhoto.filename}
        />
      ) : (
        <div className="trip-cover-empty" aria-hidden="true">
          <ImagePlus size={30} />
        </div>
      )}
      <div className="trip-cover-scrim" />
      <div className="trip-cover-content">
        <span className="soft-kicker">Private trip memory</span>
        <h2>{title}</h2>
        <p>{description}</p>
        <div className="cover-stats">
          <span>
            <strong>{photoCount}</strong>
            Photos
          </span>
          <span>
            <strong>{locatedCount}</strong>
            Places
          </span>
          <span>
            <strong>{analyzedCount}</strong>
            Memories
          </span>
        </div>
        <div className="cover-actions">
          <button
            className="cover-primary"
            type="button"
            disabled={analyzeDisabled}
            onClick={() => onAnalyze(primaryMode)}
          >
            <Sparkles size={17} aria-hidden="true" />
            <span>{buttonLabel}</span>
          </button>
          {trip ? (
            <details className="cover-menu">
              <summary title="More trip actions">
                <MoreHorizontal size={18} aria-hidden="true" />
              </summary>
              <div className="cover-menu-popover">
                <button
                  type="button"
                  disabled={!selectedPhoto || selectedPhoto.id === trip.cover_photo_id}
                  onClick={() => selectedPhoto && onSetCover(selectedPhoto.id)}
                >
                  <Pin size={15} aria-hidden="true" />
                  <span>Use selected photo as cover</span>
                </button>
                {analyzedCount > 0 && missingAnalysisCount > 0 ? (
                  <button
                    type="button"
                    disabled={analyzeDisabled}
                    onClick={() => onAnalyze("all")}
                  >
                    <RotateCcw size={15} aria-hidden="true" />
                    <span>Develop all photos again</span>
                  </button>
                ) : null}
                <button type="button" onClick={onExportMarkdown}>
                  <Download size={15} aria-hidden="true" />
                  <span>Export Markdown</span>
                </button>
                <button type="button" onClick={onExportZip}>
                  <Download size={15} aria-hidden="true" />
                  <span>Export ZIP dossier</span>
                </button>
              </div>
            </details>
          ) : null}
          <span className="cover-privacy">
            <MapPin size={14} aria-hidden="true" />
            EXIF coordinates only
          </span>
        </div>
      </div>
      {photos.length > 0 ? (
        <div className="cover-contact-strip" aria-label="Trip photo contact strip">
          {photos.slice(0, 5).map((photo) => (
            <img
              key={photo.id}
              src={assetUrl(photo.image_url)}
              alt={photo.analysis?.memory_caption || photo.filename}
            />
          ))}
        </div>
      ) : null}
      {job ? (
        <CoverJob
          job={job}
          onCancelJob={onCancelJob}
          onRetryJob={onRetryJob}
        />
      ) : null}
    </section>
  );
}

function CoverJob({
  job,
  onCancelJob,
  onRetryJob
}: {
  job: AnalysisJob;
  onCancelJob: () => void;
  onRetryJob: () => void;
}) {
  const percent = jobPercent(job);
  const detail = jobDetail(job);
  const stepCount = jobStepCount(job);
  const remaining = jobRemaining(job);
  const running = job.status === "queued" || job.status === "running";
  const retryable = job.status === "failed" || job.status === "canceled";
  const cancelLabel =
    job.status === "running" ? "Cancel after current step" : "Cancel";
  return (
    <div className={`cover-job ${job.status}`}>
      <div>
        <strong>{jobStage(job)}</strong>
        <span>{percent}%</span>
      </div>
      <p className="job-step-line">{detail}</p>
      <progress max={100} value={percent} />
      {stepCount || remaining ? (
        <div className="job-meta-row">
          {stepCount ? <span>{stepCount}</span> : null}
          {remaining ? <span>{remaining}</span> : null}
        </div>
      ) : null}
      {running ? (
        <button type="button" onClick={onCancelJob}>
          {cancelLabel}
        </button>
      ) : null}
      {retryable ? (
        <button type="button" onClick={onRetryJob}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
