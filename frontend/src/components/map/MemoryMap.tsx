import { Link } from "react-router-dom";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import type { LatLngExpression } from "leaflet";
import { assetUrl, type Photo } from "../../api/client";

export function MemoryMap({ photos }: { photos: Photo[] }) {
  const locatedPhotos = photos.filter(
    (photo) => photo.latitude !== null && photo.longitude !== null
  );
  const unlocatedCount = photos.length - locatedPhotos.length;
  const focusPhoto = locatedPhotos[0] ?? null;
  const center: LatLngExpression = focusPhoto
    ? [focusPhoto.latitude!, focusPhoto.longitude!]
    : [25.03, -77.4];

  return (
    <div className="map-frame">
      <MapContainer
        key={`${focusPhoto?.id ?? "none"}-${locatedPhotos.length}`}
        center={center}
        zoom={locatedPhotos.length > 0 ? 11 : 6}
        scrollWheelZoom
        className="leaflet-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
        />
        {locatedPhotos.map((photo) => (
          <Marker key={photo.id} position={[photo.latitude!, photo.longitude!]}>
            <Popup className="memory-popup">
              <img src={assetUrl(photo.image_url)} alt="" />
              <strong>{photo.analysis?.memory_caption || photo.filename}</strong>
              <p>{photo.analysis?.place_type || "GPS from EXIF metadata"}</p>
              <Link to={`/photos/${photo.id}`}>Open photo</Link>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      {locatedPhotos.length === 0 ? (
        <div className="map-empty">
          <span aria-hidden="true" />
          <strong>No GPS trail yet</strong>
          <p>
            Photos without EXIF coordinates still become memories, but pins only
            come from metadata.
          </p>
        </div>
      ) : null}
      {locatedPhotos.length > 0 && unlocatedCount > 0 ? (
        <div className="map-note">
          {unlocatedCount} photo{unlocatedCount === 1 ? "" : "s"} without GPS
        </div>
      ) : null}
    </div>
  );
}
