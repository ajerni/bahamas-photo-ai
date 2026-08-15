import { useState } from "react";
import { CircleAlert, RefreshCw, Sparkles, X } from "lucide-react";
import { useTrip } from "../../trip/TripProvider";
import { isJobActive, jobPercent, jobStage, jobStepCount } from "../../trip/jobStatus";

export function JobProgressBar() {
  const { job, dismissJob, retryFailedJob } = useTrip();
  const [retrying, setRetrying] = useState(false);

  if (!job || (!isJobActive(job) && job.status !== "failed")) {
    return null;
  }

  const failed = job.status === "failed";
  const percent = failed ? 100 : jobPercent(job);
  const steps = jobStepCount(job);

  return (
    <div className={`job-progress ${failed ? "failed" : ""}`} role="status">
      <div className="job-progress-track">
        <span style={{ width: `${percent}%` }} />
      </div>
      <div className="job-progress-label">
        {failed ? (
          <CircleAlert size={13} aria-hidden="true" />
        ) : (
          <Sparkles size={13} aria-hidden="true" />
        )}
        <strong>{jobStage(job)}</strong>
        {failed ? <span>{job.error}</span> : steps ? <span>{steps}</span> : null}
        {failed ? (
          <span className="job-progress-actions">
            <button
              type="button"
              disabled={retrying}
              onClick={() => {
                setRetrying(true);
                void retryFailedJob().finally(() => setRetrying(false));
              }}
            >
              <RefreshCw size={12} aria-hidden="true" />
              Try again
            </button>
            <button type="button" onClick={dismissJob} aria-label="Dismiss">
              <X size={12} aria-hidden="true" />
            </button>
          </span>
        ) : null}
      </div>
    </div>
  );
}
