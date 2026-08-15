import { useEffect, useState } from "react";
import { X } from "lucide-react";
import type { PhotoImportResponse } from "../../api/client";
import { useTrip } from "../../trip/TripProvider";
import { UploadPanel } from "../upload/UploadPanel";
import { SettingsPanel } from "../settings/SettingsPanel";

export function BurgerMenu({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { upload, loading } = useTrip();
  const [importResult, setImportResult] = useState<PhotoImportResponse | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <aside
        className="sheet"
        role="dialog"
        aria-label="Menu"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="sheet-header">
          <h2>Menu</h2>
          <button type="button" onClick={onClose} aria-label="Close menu">
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <div className="sheet-body">
          <section className="settings-section">
            <h3>Add photos</h3>
            <p className="settings-hint">
              New photos start remembering themselves right away.
            </p>
            <UploadPanel
              disabled={loading}
              importResult={importResult}
              onUpload={(files) => {
                void upload(files).then(setImportResult);
              }}
            />
          </section>

          <SettingsPanel />
        </div>
      </aside>
    </div>
  );
}
