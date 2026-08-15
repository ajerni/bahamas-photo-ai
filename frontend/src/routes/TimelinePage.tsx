import { MemoryTimeline } from "../components/timeline/MemoryTimeline";
import { useTrip } from "../trip/TripProvider";

export function TimelinePage() {
  const { photos } = useTrip();

  return (
    <div className="page timeline-page">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Timeline</span>
          <h2>When it happened</h2>
        </div>
        <span className="count-pill">{photos.length} photos</span>
      </div>

      <MemoryTimeline photos={photos} />
    </div>
  );
}
