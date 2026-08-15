import type { AnalysisJob } from "../../api/client";

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
    return "Ready";
  }
  if (job.status === "failed") {
    return "Needs attention";
  }
  if (job.status === "canceled") {
    return "Canceled";
  }
  if (job.status === "cancel_requested") {
    return "Canceling";
  }
  if (job.completed_steps <= 0) {
    return "Reading photos";
  }
  if (job.total_steps > 0 && job.completed_steps >= job.total_steps - 1) {
    return "Writing trip memory";
  }
  return "Finding moments";
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
  return `${completed} of ${job.total_steps} workflow steps`;
}

export function jobRemaining(job: AnalysisJob): string | null {
  if (job.total_steps <= 0 || job.status === "completed") {
    return null;
  }
  const remaining = Math.max(job.total_steps - job.completed_steps, 0);
  if (remaining === 0) {
    return "Finishing up";
  }
  return `${remaining} step${remaining === 1 ? "" : "s"} left`;
}
