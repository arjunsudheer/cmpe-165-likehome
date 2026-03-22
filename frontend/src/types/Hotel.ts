export interface Hotel {
  id: number;
  name: string;
  location: string;
  rating: number;
  description: string;
  photos?: string[];
  pricePerNight: number;
  amenities: string[];
  address?: string;
  reviewCount?: number;
}
