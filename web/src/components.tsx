import { Link } from "react-router-dom";
import { ArrowUpRight, Music2 } from "lucide-react";
import type { ArtworkCard } from "./types";

export function ArtworkTile({ artwork }: { artwork: ArtworkCard }) {
  return <Link className="group artwork-tile" to={`/artwork/${artwork.smk_entity_id}`}>
    <div className="tile-image-wrap">
      {artwork.image_thumbnail ? <img className="tile-image" src={artwork.image_thumbnail} alt={artwork.display_title} loading="lazy" /> : <div className="image-fallback"><Music2 /></div>}
      <span className="tile-arrow"><ArrowUpRight size={18} /></span>
    </div>
    <div className="pt-3">
      <p className="eyebrow">{artwork.object_number}</p>
      <h3 className="tile-title">{artwork.display_title}</h3>
      <p className="muted line-clamp-1">{artwork.artist_display || "Unknown artist"}{artwork.date_text ? ` · ${artwork.date_text}` : ""}</p>
    </div>
  </Link>;
}

export function PaletteBar({ palette }: { palette: Array<{ hex: string; weight: number }> }) {
  return <div className="palette-wrap" aria-label="Weighted colour palette">
    <div className="palette-bar">{palette.map((color) => <div key={color.hex} style={{ background: color.hex, flexGrow: Math.max(color.weight, .025) }} title={`${color.hex} ${(color.weight * 100).toFixed(1)}%`} />)}</div>
    <div className="palette-labels">{palette.map((color) => <div key={color.hex} className="palette-label"><span className="swatch" style={{ background: color.hex }} /><span>{color.hex}</span><strong>{(color.weight * 100).toFixed(1)}%</strong></div>)}</div>
  </div>;
}

export function Loading({ label = "Loading collection" }: { label?: string }) {
  return <div className="loading"><span /><p>{label}</p></div>;
}
