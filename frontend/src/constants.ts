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

/** Gradient backgrounds used as hotel image placeholders */
export const CARD_GRADIENTS = [
  "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
  "linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)",
  "linear-gradient(135deg, #10b981 0%, #0ea5e9 100%)",
  "linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)",
  "linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)",
  "linear-gradient(135deg, #14b8a6 0%, #3b82f6 100%)",
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
