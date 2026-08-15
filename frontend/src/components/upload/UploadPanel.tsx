import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { ImagePlus, LockKeyhole, Upload } from "lucide-react";
import type { PhotoImportResponse } from "../../api/client";

type UploadPanelProps = {
  disabled: boolean;
  compact: boolean;
  importResult: PhotoImportResponse | null;
  onUpload: (files: FileList | File[]) => void;
};

export function UploadPanel({
  disabled,
  compact,
  importResult,
  onUpload
}: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (files && files.length > 0) {
      onUpload(files);
      event.target.value = "";
    }
  }

  function handleDragOver(event: DragEvent<HTMLLabelElement>) {
    if (disabled) {
      return;
    }
    event.preventDefault();
    setDragActive(true);
  }

  function handleDragLeave() {
    setDragActive(false);
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    if (disabled) {
      return;
    }
    event.preventDefault();
    setDragActive(false);
    const files = Array.from(event.dataTransfer.files).filter((file) =>
      file.type.startsWith("image/")
    );
    if (files.length > 0) {
      onUpload(files);
    }
  }

  return (
    <div className={`upload-panel ${compact ? "compact" : ""}`}>
      <div className="panel-heading">
        <div>
          <span className="soft-kicker">Photo import</span>
          <h2>{compact ? "Add more" : "Add travel photos"}</h2>
        </div>
        <button
          className="secondary-action"
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
          title="Choose photos"
        >
          <ImagePlus size={16} aria-hidden="true" />
          <span>Select</span>
        </button>
      </div>
      <label
        className={`drop-zone ${disabled ? "disabled" : ""} ${dragActive ? "drag-active" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <span className="drop-icon">
          <Upload size={24} aria-hidden="true" />
        </span>
        <strong>{compact ? "Add more photos" : "Drop travel photos here"}</strong>
        <span>JPEG, PNG, and WebP only. EXIF metadata stays local.</span>
        <em>
          <LockKeyhole size={13} aria-hidden="true" />
          No cloud upload path
        </em>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          disabled={disabled}
          onChange={handleChange}
        />
      </label>
      {importResult ? <ImportSummary result={importResult} /> : null}
    </div>
  );
}

function ImportSummary({ result }: { result: PhotoImportResponse }) {
  return (
    <div className="import-summary">
      <div>
        <span>
          <strong>{result.stored_count}</strong>
          Stored
        </span>
        <span>
          <strong>{result.duplicate_count}</strong>
          Skipped
        </span>
        <span>
          <strong>{result.rejected_count}</strong>
          Rejected
        </span>
      </div>
      {result.results.some((item) => item.status !== "stored") ? (
        <ul>
          {result.results
            .filter((item) => item.status !== "stored")
            .slice(0, 4)
            .map((item) => (
              <li key={`${item.filename}-${item.status}`}>
                <strong>{item.filename}</strong>
                <span>{item.detail ?? item.status}</span>
              </li>
            ))}
        </ul>
      ) : null}
    </div>
  );
}
