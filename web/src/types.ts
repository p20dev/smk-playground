export type ArtworkCard = {
  smk_entity_id: string; object_number: string; display_title: string;
  artist_display?: string; date_text?: string; classification?: string;
  image_thumbnail?: string; centroid_chroma?: number; dominant_color_hex?: string;
};

export type Tone = {
  profile: string; version: string; available: boolean; reason?: string; note?: string;
  octave?: number; midi?: number; frequency_hz?: number; velocity?: number; attack?: number;
  release?: number; harmonic_richness?: number; noise_amount?: number; tonal_purity?: number;
  stereo_pan?: number; explanation?: Record<string, string>;
};

export type PaletteNote = { hex: string; weight: number; note: string; octave: number;
  frequency_hz: number; velocity: number; duration_seconds: number };

export type Artwork = ArtworkCard & {
  title_da?: string; title_en?: string; image_native?: string; image_width?: number;
  image_height?: number; rights_semantic?: string; net_width_cm?: number; net_height_cm?: number;
  quality_flags: string[];
  weighted_palette: Array<{ palette_rank: number; hex: string; token_count: number; weight: number;
    oklab_l: number; oklch_c: number; oklch_h_deg?: number }>;
  weighted_features: Record<string, number | string | null>;
  sonification: { weighted_color: Tone; physical: Tone;
    palette_arpeggio: { available: boolean; notes: PaletteNote[]; explanation: string } };
  provenance: Record<string, string>;
};

export type SimilarItem = ArtworkCard & { rank: number; distance: number; active_components: string[] };
