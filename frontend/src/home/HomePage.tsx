import { useEffect, useRef, useState } from "react";
import SearchHero, {
  type SearchHeroHandle,
  type SearchValues,
} from "./SearchHero";
import HotelFilter from "./HotelFilter";
import type { Hotel } from "./Hotel";
import { CARD_GRADIENTS } from "../constants";
import "./HomePage.css";
import { useSearchParams } from "react-router-dom";

export type SortField = "name" | "price" | "rating" | null;
export type SortOrder = "asc" | "desc" | null;

function StarRow({ rating }: { rating: number }) {
  return (
    <span className="star-row" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          className={n <= Math.round(rating) ? "star filled" : "star"}
        >
          ★
        </span>
      ))}
    </span>
  );
}

function HotelCard({ hotel, index }: { hotel: Hotel; index: number }) {
  const gradient = CARD_GRADIENTS[index % CARD_GRADIENTS.length];
  return (
    <a
      href={`/hotel/${hotel.id}`}
      target="_blank"
      rel="noopener noreferrer"
      className="hotel-card"
    >
      <div className="hotel-card-image">
        {hotel.primary_photo ? (
          <img src={hotel.primary_photo} alt={hotel.name} loading="lazy" />
        ) : (
          <div
            className="hotel-card-placeholder"
            style={{ background: gradient }}
          />
        )}
        <div className="hotel-card-price">
          ${hotel.price_per_night.toFixed(0)}
          <span>/night</span>
        </div>
      </div>

      <div className="hotel-card-body">
        <div className="hotel-card-top">
          <div>
            <h3 className="hotel-card-name">{hotel.name}</h3>
            <p className="hotel-card-city">📍 {hotel.city}</p>
          </div>
          <div className="hotel-card-rating">
            <StarRow rating={hotel.rating} />
            <span className="rating-num">{hotel.rating.toFixed(1)}</span>
          </div>
        </div>
      </div>
    </a>
  );
}

// ✅ Updated sort helper
function sortHotels(
  hotels: Hotel[],
  field: SortField,
  order: SortOrder,
): Hotel[] {
  if (!field || !order) return hotels;

  return [...hotels].sort((a, b) => {
    let cmp = 0;
    if (field === "name") cmp = a.name.localeCompare(b.name);
    if (field === "price") cmp = a.price_per_night - b.price_per_night;
    if (field === "rating") cmp = a.rating - b.rating;
    return order === "asc" ? cmp : -cmp;
  });
}

function SortBar({
  field,
  order,
  onChange,
}: {
  field: SortField;
  order: SortOrder;
  onChange: (field: SortField, order: SortOrder) => void;
}) {
  const handleFieldClick = (f: SortField) => {
    if (f !== field) {
      onChange(f, "asc");
      return;
    }
    if (order === "asc") {
      onChange(f, "desc");
    } else if (order === "desc") {
      onChange(null, null);
    } else {
      onChange(f, "asc");
    }
  };

  const SORT_LABELS = {
    name: "Name",
    price: "Price",
    rating: "Rating",
  };

  return (
    <div className="sort-bar">
      <span className="sort-label">Sort by:</span>
      {(Object.keys(SORT_LABELS) as (keyof typeof SORT_LABELS)[]).map((f) => {
        const active = f === field;
        return (
          <button
            key={f}
            className={`sort-btn${active ? " sort-btn--active" : ""}`}
            onClick={() => handleFieldClick(f)}
          >
            {SORT_LABELS[f]}
            {active && order && (order === "asc" ? " ↑" : " ↓")}
          </button>
        );
      })}
    </div>
  );
}

export default function HomePage() {
  const heroRef = useRef<SearchHeroHandle>(null);

  const [allHotels, setAllHotels] = useState<Hotel[]>([]);
  const [filtered, setFiltered] = useState<Hotel[]>([]);
  const [displayed, setDisplayed] = useState<Hotel[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [searchParams] = useSearchParams();

  const [sortField, setSortField] = useState<SortField>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>(null);

  useEffect(() => {
    setSortField(null);
    setSortOrder(null);
  }, []);

  useEffect(() => {
    setDisplayed(sortHotels(filtered, sortField, sortOrder));
  }, [filtered, sortField, sortOrder]);

  const handleSortChange = (field: SortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);
  };

  useEffect(() => {
    fetch("/hotels/")
      .then((r) => r.json())
      .then((data) => {
        const hotels: Hotel[] = data.results ?? [];
        setAllHotels(hotels);
        setFiltered(hotels);
      })
      .catch(() => setError("Failed to load hotels."))
      .finally(() => setLoading(false));
  }, [searchParams]);

  return (
    <div className="home-page">
      <SearchHero
        ref={heroRef}
        onSearch={() => {}}
        isLoading={false}
        resultCount={null}
        filters={{ maxPrice: 1000, minRating: 0, selectedAmenities: [] }}
        sortSettings={{ sortField, sortOrder }}
      />

      <div className="home-body">
        <HotelFilter
          hotels={allHotels}
          onFilter={setFiltered}
          onFiltersChange={() => {}}
        />

        <section className="hotel-grid-section">
          <SortBar
            field={sortField}
            order={sortOrder}
            onChange={handleSortChange}
          />

          {loading ? (
            <div>Loading...</div>
          ) : (
            <div className="hotel-grid">
              {displayed.map((h, i) => (
                <HotelCard key={h.id} hotel={h} index={i} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
