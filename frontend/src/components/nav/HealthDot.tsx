import { useTrip } from "../../trip/TripProvider";

export function HealthDot() {
  const { health, healthError } = useTrip();

  const state = !health ? "offline" : health.model_available ? "ready" : "warning";
  const label = !health
    ? healthError ?? "Backend offline"
    : health.model_available
      ? `${health.model} ready · ${health.database}`
      : health.model_error ?? `Model ${health.model_status}`;

  return (
    <span className={`health-dot ${state}`} title={label}>
      <span aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </span>
  );
}
