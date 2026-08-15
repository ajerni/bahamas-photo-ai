import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { divIcon, type LatLngExpression, type Marker as LMarker } from "leaflet";
import { assetUrl, type Photo } from "../../api/client";

// One shared instance each: a fresh icon on every render would make react-leaflet
// rebuild the marker's DOM and close the popup we just opened.
const FOCUS_ICON = divIcon({ className: "marker-focus", iconSize: [18, 18] });
const PIN_ICON = divIcon({ className: "map-pin", iconSize: [14, 14] });

function FlyToMarker({
  photo,
  markerRef
}: {
  photo: Photo;
  markerRef: React.RefObject<LMarker | null>;
}) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([photo.latitude!, photo.longitude!], 14, { duration: 1 });
    const timer = window.setTimeout(() => markerRef.current?.openPopup(), 1100);
    return () => window.clearTimeout(timer);
  }, [map, photo.id, photo.latitude, photo.longitude, markerRef]);
  return null;
}

export function MemoryMap({
  photos,
  focusPhotoId
}: {
  photos: Photo[];
  focusPhotoId?: number | null;
}) {
  const locatedPhotos = photos.filter(
    (photo) => photo.latitude !== null && photo.longitude !== null
  );
  const unlocatedCount = photos.length - locatedPhotos.length;
  const focusPhoto = focusPhotoId
    ? (locatedPhotos.find((p) => p.id === focusPhotoId) ?? null)
    : null;
  const initialPhoto = focusPhoto ?? locatedPhotos[0] ?? null;
  const center: LatLngExpression = initialPhoto
    ? [initialPhoto.latitude!, initialPhoto.longitude!]
    : [25.03, -77.4];
  const focusMarkerRef = useRef<LMarker | null>(null);

  return (
    <div className="map-frame">
      <MapContainer
        key={`${locatedPhotos[0]?.id ?? "none"}-${locatedPhotos.length}`}
        center={center}
        zoom={locatedPhotos.length > 0 ? 11 : 6}
        scrollWheelZoom
        className="leaflet-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
        />
        {focusPhoto ? (
          <FlyToMarker photo={focusPhoto} markerRef={focusMarkerRef} />
        ) : null}
        {locatedPhotos.map((photo) => (
          <Marker
            key={photo.id}
            position={[photo.latitude!, photo.longitude!]}
            ref={photo.id === focusPhotoId ? focusMarkerRef : null}
            icon={photo.id === focusPhotoId ? FOCUS_ICON : PIN_ICON}
          >
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
