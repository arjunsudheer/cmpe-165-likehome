/**
 * Password reset API (backend to implement).
 * Forgot: POST JSON `{ email }` → 200 `{ message }`, optional `{ reset_token }` for dev.
 * Reset: POST JSON `{ token, password }` → 200 `{ message }` or 4xx `{ error }`.
 */
export const AUTH_API_FORGOT_PASSWORD = "/auth/forgot-password";
export const AUTH_API_RESET_PASSWORD = "/auth/reset-password";

/** 100 points = $1.00 when redeeming */
export const POINTS_REDEEM_RATE = 100;

/** 10 points earned per $1 spent */
export const POINTS_EARN_RATE = 10;

/** Room price multipliers relative to hotel base price */
export const ROOM_MULTIPLIERS: Record<string, number> = {
  SINGLE: 0.85,
  DOUBLE: 1.0,
  TRIPLE: 1.35,
  QUAD: 1.7,
};

export const ROOM_LABELS: Record<string, string> = {
  SINGLE: "Single",
  DOUBLE: "Double",
  TRIPLE: "Triple",
  QUAD: "Quad",
};

/** Gradient backgrounds used as hotel image placeholders — Jigsaw Nights palette */
export const CARD_GRADIENTS = [
  "linear-gradient(135deg, #1a3a6b 0%, #0d2147 100%)",
  "linear-gradient(135deg, #0a2a5e 0%, #30c9d4 100%)",
  "linear-gradient(135deg, #f5a623 0%, #d4891a 60%, #92400e 100%)",
  "linear-gradient(135deg, #162d52 0%, #30c9d4 80%, #22b0ba 100%)",
  "linear-gradient(135deg, #0d1f3c 0%, #1a3a6b 50%, #f5a623 100%)",
  "linear-gradient(135deg, #1e3d6e 0%, #0d2147 50%, #30c9d4 100%)",
];

export const AMENITY_ICONS: Record<string, string> = {
  "Free WiFi": "📶",
  "Pool": "🏊",
  "Fitness Center": "🏋️",
  "Gym": "🏋️",
  "Parking": "🅿️",
  "Breakfast Included": "🍳",
  "Spa": "💆",
  "Airport Shuttle": "🚌",
  "Restaurant": "🍽️",
  "Pet Friendly": "🐾",
  "Beach Access": "🏖️",
  "Bar": "🍸",
  "Family Rooms": "👨‍👩‍👧",
  "Business Center": "💼",
  "Room Service": "🛎️",
  "Laundry Service": "🧺",
};
