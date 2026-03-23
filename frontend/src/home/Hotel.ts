/** Matches the /hotels/ and /hotels/search API response shape */
export interface Hotel {
  id: number;
  name: string;
  city: string;
  address: string;
  price_per_night: number;
  rating: number;
  review_count: number;
  primary_photo: string | null;
  amenities: string[];
}
