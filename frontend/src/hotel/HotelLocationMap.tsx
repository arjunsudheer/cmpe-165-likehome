import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type NearbyPlace = {
  name: string;
  distanceMeters: number;
};

type NearbyResult = {
  restaurants: NearbyPlace[];
  gasStations: NearbyPlace[];
};

type HotelMapData = {
  id: number;
  name: string;
  city: string;
  address: string;
  price_per_night: number;
  rating?: number;
  review_count?: number;
  latitude?: number;
  longitude?: number;
};

const DEFAULT_CENTER: [number, number] = [37.7749, -122.4194];
const GEO_CACHE_PREFIX = "lh_geo_";
const NEARBY_CACHE_PREFIX = "lh_nearby_";
const NEARBY_RADIUS_METERS = 1200;
const MAX_NEARBY_ITEMS = 3;

const HOTEL_MARKER_ICON = L.divIcon({
  className: "hdp-map-marker-wrap",
  html: '<span class="hdp-map-marker-dot" aria-hidden="true"></span>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

function geoCacheKey(query: string): string {
  return `${GEO_CACHE_PREFIX}${query.toLowerCase()}`;
}

function nearbyCacheKey(lat: number, lon: number): string {
  return `${NEARBY_CACHE_PREFIX}${lat.toFixed(4)}_${lon.toFixed(4)}`;
}

function distanceMeters(aLat: number, aLon: number, bLat: number, bLon: number): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const earthRadiusMeters = 6371000;
  const dLat = toRad(bLat - aLat);
  const dLon = toRad(bLon - aLon);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) * Math.sin(dLon / 2) ** 2;
  return Math.round(earthRadiusMeters * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
}

async function geocodeAddress(query: string): Promise<[number, number] | null> {
  try {
    const cached = localStorage.getItem(geoCacheKey(query));
    if (cached) {
      const parsed = JSON.parse(cached) as { lat?: number; lon?: number };
      if (typeof parsed.lat === "number" && typeof parsed.lon === "number") {
        return [parsed.lat, parsed.lon];
      }
    }
  } catch {
    // Ignore cache parse failures.
  }

  const url = new URL("/hotels/geocode", window.location.origin);
  url.searchParams.set("q", query);
  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  if (!res.ok) return null;
  const data = (await res.json()) as { result?: { lat?: number; lon?: number } | null };
  if (!data.result) return null;

  const lat = Number(data.result.lat);
  const lon = Number(data.result.lon);
  if (Number.isNaN(lat) || Number.isNaN(lon)) return null;

  try {
    localStorage.setItem(geoCacheKey(query), JSON.stringify({ lat, lon }));
  } catch {
    // Ignore quota issues.
  }
  return [lat, lon];
}

function parseNearby(
  elements: Array<{ lat?: number; lon?: number; tags?: Record<string, string> }>,
  center: [number, number]
): NearbyResult {
  const restaurants: NearbyPlace[] = [];
  const gasStations: NearbyPlace[] = [];
  const [lat, lon] = center;

  for (const element of elements) {
    if (typeof element.lat !== "number" || typeof element.lon !== "number") continue;
    const amenity = element.tags?.amenity;
    if (amenity !== "restaurant" && amenity !== "fuel") continue;
    const place: NearbyPlace = {
      name: element.tags?.name ?? (amenity === "fuel" ? "Gas station" : "Restaurant"),
      distanceMeters: distanceMeters(lat, lon, element.lat, element.lon),
    };
    if (amenity === "restaurant") restaurants.push(place);
    else gasStations.push(place);
  }

  restaurants.sort((a, b) => a.distanceMeters - b.distanceMeters);
  gasStations.sort((a, b) => a.distanceMeters - b.distanceMeters);
  return {
    restaurants: restaurants.slice(0, MAX_NEARBY_ITEMS),
    gasStations: gasStations.slice(0, MAX_NEARBY_ITEMS),
  };
}

async function fetchNearbyPlaces(center: [number, number]): Promise<NearbyResult> {
  const [lat, lon] = center;
  const key = nearbyCacheKey(lat, lon);
  try {
    const cached = localStorage.getItem(key);
    if (cached) return JSON.parse(cached) as NearbyResult;
  } catch {
    // Ignore invalid cache values.
  }

  const url = new URL("/hotels/nearby", window.location.origin);
  url.searchParams.set("lat", String(lat));
  url.searchParams.set("lon", String(lon));
  url.searchParams.set("radius", String(NEARBY_RADIUS_METERS));
  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error("nearby lookup failed");
  const data = (await res.json()) as {
    elements?: Array<{ lat?: number; lon?: number; tags?: Record<string, string> }>;
  };
  const parsed = parseNearby(data.elements ?? [], center);
  try {
    localStorage.setItem(key, JSON.stringify(parsed));
  } catch {
    // Ignore cache write failures.
  }
  return parsed;
}

function NearbyBlock({ title, items }: { title: string; items: NearbyPlace[] }) {
  return (
    <div>
      <h4 className="hdp-map-nearby-title">{title}</h4>
      {items.length === 0 ? (
        <p className="hdp-map-nearby-empty">No nearby results.</p>
      ) : (
        <ul className="hdp-map-nearby-list">
          {items.map((item) => (
            <li key={`${title}-${item.name}-${item.distanceMeters}`}>
              {item.name} ({item.distanceMeters}m)
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function HotelLocationMap({ hotel }: { hotel: HotelMapData }) {
  const [coords, setCoords] = useState<[number, number] | null>(null);
  const [isApproximateLocation, setIsApproximateLocation] = useState(false);
  const [nearby, setNearby] = useState<NearbyResult | null>(null);
  const [loadingMap, setLoadingMap] = useState(true);
  const [loadingNearby, setLoadingNearby] = useState(false);
  const [mapError, setMapError] = useState("");
  const [nearbyError, setNearbyError] = useState("");

  useEffect(() => {
    let active = true;
    const resolve = async () => {
      setLoadingMap(true);
      setMapError("");
      setNearbyError("");
      setNearby(null);
      setIsApproximateLocation(false);
      try {
        let position: [number, number] | null =
          typeof hotel.latitude === "number" && typeof hotel.longitude === "number"
            ? [hotel.latitude, hotel.longitude]
            : await geocodeAddress(`${hotel.address}, ${hotel.city}`);

        // Fallback: if the exact hotel address cannot be geocoded, use city center.
        if (!position) {
          position = await geocodeAddress(hotel.city);
          if (position) setIsApproximateLocation(true);
        }

        // Last fallback so the map still renders for synthetic/fake test data.
        if (!position) {
          position = DEFAULT_CENTER;
          setIsApproximateLocation(true);
        }

        if (!position) {
          if (active) {
            setMapError("Map location unavailable for this hotel.");
            setLoadingMap(false);
          }
          return;
        }
        const tuple = position as [number, number];
        if (!active) return;
        setCoords(tuple);

        setLoadingMap(false);
        setLoadingNearby(true);
        try {
          const nearbyData = await fetchNearbyPlaces(tuple);
          if (!active) return;
          setNearby(nearbyData);
        } catch {
          if (active) setNearbyError("Nearby places unavailable right now.");
        } finally {
          if (active) setLoadingNearby(false);
        }
      } catch {
        if (active) {
          setMapError("Failed to load map data.");
          setLoadingMap(false);
          setLoadingNearby(false);
        }
      }
    };
    void resolve();
    return () => {
      active = false;
    };
  }, [hotel.address, hotel.city, hotel.latitude, hotel.longitude]);

  const center = useMemo<[number, number]>(() => coords ?? DEFAULT_CENTER, [coords]);

  return (
    <section className="hdp-section hdp-section-full">
      <h2 className="hdp-section-title">Location & nearby places</h2>
      {loadingMap && <p className="hdp-map-status">Loading map...</p>}
      {mapError && <p className="hdp-map-status hdp-map-error">{mapError}</p>}
      {!loadingMap && !mapError && coords && (
        <>
          {isApproximateLocation && (
            <p className="hdp-map-status">
              Showing approximate location for this hotel.
            </p>
          )}
          <MapContainer center={center} zoom={14} scrollWheelZoom className="hdp-map-container">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker position={coords} icon={HOTEL_MARKER_ICON}>
              <Popup>
                <div className="hdp-map-popup-card">
                  <strong className="hdp-map-popup-title">{hotel.name}</strong>
                  <p className="hdp-map-popup-location">
                    {hotel.address}, {hotel.city}
                  </p>
                  <p className="hdp-map-popup-meta">
                    ${hotel.price_per_night.toFixed(0)} / night
                    {typeof hotel.rating === "number" ? ` · ${hotel.rating.toFixed(1)} ★` : ""}
                    {typeof hotel.review_count === "number" ? ` (${hotel.review_count} reviews)` : ""}
                  </p>
                  <div className="hdp-map-popup-actions">
                    <a href={`/hotel/${hotel.id}#reviews`}>View reviews</a>
                    <a href={`/booking/${hotel.id}`}>Reserve</a>
                  </div>
                </div>
              </Popup>
            </Marker>
          </MapContainer>
          {loadingNearby && <p className="hdp-map-status">Loading nearby places...</p>}
          {nearbyError && <p className="hdp-map-status hdp-map-error">{nearbyError}</p>}
          {nearby && (
            <div className="hdp-map-nearby-grid">
              <NearbyBlock title="Restaurants" items={nearby.restaurants} />
              <NearbyBlock title="Gas stations" items={nearby.gasStations} />
            </div>
          )}
        </>
      )}
    </section>
  );
}
