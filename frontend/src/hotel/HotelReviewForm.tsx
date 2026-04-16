import { useState } from "react";
import "./HotelDetailsPage.css";

const TITLE_MAX = 20;
const CONTENT_MAX = 255;

function StarRatingInput({
  value,
  onChange,
}: {
  value: number;
  onChange: (n: number) => void;
}) {
  return (
    <div className="hdp-review-form-stars" role="group" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          className={`hdp-star-btn${n <= value ? " active" : ""}`}
          onClick={() => onChange(n)}
          aria-pressed={n <= value}
          aria-label={`${n} star${n === 1 ? "" : "s"}`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

export interface HotelReviewFormProps {
  hotelId: number;
  authHeader: Record<string, string>;
  onSuccess: () => void;
}

export default function HotelReviewForm({ hotelId, authHeader, onSuccess }: HotelReviewFormProps) {
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
      setError("Choose a rating from 1 to 5.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`/hotels/${hotelId}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeader },
        body: JSON.stringify({
          rating,
          title: title.trim() || "No title",
          content: content.trim() || "No content",
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Could not post review.");
        return;
      }
      setTitle("");
      setContent("");
      setRating(5);
      onSuccess();
    } catch {
      setError("Network error — please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="hdp-review-form" onSubmit={handleSubmit}>
      <h3 className="hdp-review-form-title">Write a review</h3>
      <p className="hdp-review-form-hint">Share your stay — title up to {TITLE_MAX} characters.</p>

      {error && <div className="alert alert-error hdp-review-form-error">{error}</div>}

      <div className="form-group">
        <span className="form-label">Rating</span>
        <StarRatingInput value={rating} onChange={setRating} />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="review-title">Title</label>
        <input
          id="review-title"
          className="form-input"
          maxLength={TITLE_MAX}
          value={title}
          onChange={(ev) => setTitle(ev.target.value)}
          placeholder="Short headline"
          autoComplete="off"
        />
        <span className="hdp-review-form-counter">{title.length}/{TITLE_MAX}</span>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="review-content">Your experience</label>
        <textarea
          id="review-content"
          className="form-input hdp-review-form-textarea"
          maxLength={CONTENT_MAX}
          rows={4}
          value={content}
          onChange={(ev) => setContent(ev.target.value)}
          placeholder="What stood out?"
        />
        <span className="hdp-review-form-counter">{content.length}/{CONTENT_MAX}</span>
      </div>

      <button type="submit" className="btn btn-primary hdp-review-form-submit" disabled={submitting}>
        {submitting ? "Posting…" : "Post review"}
      </button>
    </form>
  );
}
