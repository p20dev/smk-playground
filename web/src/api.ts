import type { Artwork, ArtworkCard, SimilarItem } from "./types";

async function get<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export const api = {
  stats: () => get<{ artwork_count: number; weighted_palette_count: number; physical_geometry_count: number }>("/api/stats"),
  search: (q = "", offset = 0) => get<{ total: number; items: ArtworkCard[] }>(`/api/artworks?q=${encodeURIComponent(q)}&limit=24&offset=${offset}`),
  random: () => get<ArtworkCard>("/api/artworks/random"),
  artwork: (id: string) => get<Artwork>(`/api/artworks/${encodeURIComponent(id)}`),
  similar: (id: string, profile: string, limit = 10) =>
    get<{ profile: string; cached: boolean; items: SimilarItem[] }>(`/api/artworks/${encodeURIComponent(id)}/similar?profile=${profile}&limit=${limit}`),
};
