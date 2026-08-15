import type { AnalysisJob } from "../api/client";

export function isJobActive(job: AnalysisJob | null): boolean {
  return (
    job !== null &&
    (job.status === "queued" ||
      job.status === "running" ||
      job.status === "cancel_requested")
  );
}

export function jobPercent(job: AnalysisJob): number {
  if (job.total_steps > 0) {
    return Math.min(
      100,
      Math.max(0, Math.round((job.completed_steps / job.total_steps) * 100))
    );
  }
  return job.status === "completed" ? 100 : 0;
}

export function jobStage(job: AnalysisJob): string {
  if (job.status === "completed") {
    return "Memories ready";
  }
  if (job.status === "failed") {
    return "Something went wrong";
  }
  if (job.status === "canceled") {
    return "Stopped";
  }
  if (job.status === "cancel_requested") {
    return "Stopping";
  }
  return "Remembering your photos";
}

export function jobDetail(job: AnalysisJob): string {
  if (job.error) {
    return job.error;
  }
  return job.current_step || jobStage(job);
}

export function jobStepCount(job: AnalysisJob): string | null {
  if (job.total_steps <= 0) {
    return null;
  }
  const completed = Math.min(job.completed_steps, job.total_steps);
  return `${completed} of ${job.total_steps}`;
}
