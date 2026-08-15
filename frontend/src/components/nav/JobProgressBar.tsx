import { CircleAlert, Sparkles } from "lucide-react";
import { useTrip } from "../../trip/TripProvider";
import { isJobActive, jobPercent, jobStage, jobStepCount } from "../../trip/jobStatus";

export function JobProgressBar() {
  const { job } = useTrip();

  if (!job || (!isJobActive(job) && job.status !== "failed")) {
    return null;
  }

  const percent = jobPercent(job);
  const steps = jobStepCount(job);
  const failed = job.status === "failed";

  return (
    <div className={`job-progress ${failed ? "failed" : ""}`} role="status">
      <div className="job-progress-track">
        <span style={{ width: `${failed ? 100 : percent}%` }} />
      </div>
      <div className="job-progress-label">
        {failed ? (
          <CircleAlert size={13} aria-hidden="true" />
        ) : (
          <Sparkles size={13} aria-hidden="true" />
        )}
        <strong>{jobStage(job)}</strong>
        {failed ? <span>{job.error}</span> : steps ? <span>{steps}</span> : null}
      </div>
    </div>
  );
}
