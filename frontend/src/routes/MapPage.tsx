import { MemoryMap } from "../components/map/MemoryMap";
import { useTrip } from "../trip/TripProvider";

export function MapPage() {
  const { photos } = useTrip();
  const mapped = photos.filter(
    (photo) => photo.latitude !== null && photo.longitude !== null
  ).length;

  return (
    <div className="page map-page">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Places</span>
          <h2>Where you were</h2>
        </div>
        <span className="count-pill">{mapped} pinned</span>
      </div>

      <MemoryMap photos={photos} />
    </div>
  );
}
