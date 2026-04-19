export const SAVED_SEARCHES_KEY = "lh_saved_searches";

export interface SavedSearch {
  id: string;
  destination: string;
  checkIn: string;
  checkOut: string;
  guests: number;
  savedAt: string;
}

export function readSavedSearches(): SavedSearch[] {
  try {
    const raw = localStorage.getItem(SAVED_SEARCHES_KEY);
    return raw ? (JSON.parse(raw) as SavedSearch[]) : [];
  } catch {
    return [];
  }
}
