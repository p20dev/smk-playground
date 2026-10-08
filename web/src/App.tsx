import { FormEvent, useEffect, useState } from "react";
import { Link, NavLink, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { ChevronLeft, Dices, Headphones, Pause, Play, Search, Sparkles } from "lucide-react";
import { api } from "./api";
import { playArpeggio, playTone, stopAudio } from "./audio";
import { ArtworkTile, Loading, PaletteBar } from "./components";
import type { Artwork, ArtworkCard, SimilarItem } from "./types";

function Shell({ children }: { children: React.ReactNode }) {
  return <><header className="site-header"><Link to="/" className="brand"><span className="brand-mark" />SMK Playground</Link><nav><NavLink to="/">Explore</NavLink><NavLink to="/about">About</NavLink></nav></header>{children}<footer><span>SMK open data, transformed with care.</span><span>Colour → sound is an artistic mapping.</span></footer></>;
}

function Home() {
  const [query, setQuery] = useState(""); const [items, setItems] = useState<ArtworkCard[]>([]);
  const [stats, setStats] = useState<{ artwork_count: number; weighted_palette_count: number; physical_geometry_count: number }>();
  const [loading, setLoading] = useState(true); const navigate = useNavigate();
  const load = (q = "") => { setLoading(true); api.search(q).then((r) => setItems(r.items)).finally(() => setLoading(false)); };
  useEffect(() => { load(); api.stats().then(setStats); }, []);
  const submit = (event: FormEvent) => { event.preventDefault(); load(query); };
  const surprise = () => api.random().then((art) => navigate(`/artwork/${art.smk_entity_id}`));
  return <Shell><main><section className="hero"><div><p className="kicker"><Sparkles size={14} /> An experimental colour archive</p><h1>See art.<br /><em>Hear colour.</em></h1><p className="hero-copy">Explore 27,254 open artworks from SMK through weighted palettes, perceptual colour and deterministic sound.</p><form className="search-box" onSubmit={submit}><Search /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search title, artist, object number…" aria-label="Search artworks" /><button>Search</button></form><button className="text-button" onClick={surprise}><Dices size={17} /> Surprise me</button></div><div className="hero-orbit" aria-hidden="true"><span /><span /><span /><div className="tone-dot"><Headphones /></div></div></section>{stats && <section className="stat-strip"><div><strong>{stats.artwork_count.toLocaleString()}</strong><span>open works</span></div><div><strong>{stats.weighted_palette_count.toLocaleString()}</strong><span>weighted palettes</span></div><div><strong>{stats.physical_geometry_count.toLocaleString()}</strong><span>measured works</span></div></section>}<section className="collection"><div className="section-heading"><p className="eyebrow">The collection</p><h2>{query ? `Results for “${query}”` : "A field of colour"}</h2></div>{loading ? <Loading /> : <div className="art-grid">{items.map((item) => <ArtworkTile key={item.smk_entity_id} artwork={item} />)}</div>}</section></main></Shell>;
}

const profileNames: Record<string, string> = { color: "Color", visual: "Visual character", geometry: "Physical geometry", "weighted-color": "Deep weighted color" };
function SimilarWorks({ id }: { id: string }) {
  const [profile, setProfile] = useState("color"); const [items, setItems] = useState<SimilarItem[]>([]);
  const [loading, setLoading] = useState(false); const [loaded, setLoaded] = useState<Record<string, boolean>>({});
  const load = (next: string) => { setProfile(next); if (next === "weighted-color" && !loaded[next]) return; setLoading(true); api.similar(id, next).then((r) => { setItems(r.items); setLoaded((x) => ({ ...x, [next]: true })); }).finally(() => setLoading(false)); };
  useEffect(() => load("color"), [id]);
  return <section className="similar-section"><div className="section-heading"><p className="eyebrow">Connections</p><h2>Works nearby</h2></div><div className="tabs">{Object.entries(profileNames).map(([key, label]) => <button className={profile === key ? "active" : ""} key={key} onClick={() => load(key)}>{label}</button>)}</div>{profile === "weighted-color" && !loaded[profile] ? <div className="deep-callout"><div><strong>Deep palette comparison</strong><p>Exact transport across weighted colours takes around 12 seconds the first time, then it is cached.</p></div><button onClick={() => { setLoading(true); api.similar(id, profile).then((r) => { setItems(r.items); setLoaded((x) => ({ ...x, [profile]: true })); }).finally(() => setLoading(false)); }}>Run deep comparison</button></div> : loading ? <Loading label="Comparing visual features" /> : <div className="similar-grid">{items.map((item) => <div key={item.smk_entity_id}><ArtworkTile artwork={item} /><p className="distance">#{item.rank} · distance {item.distance.toFixed(4)}</p></div>)}</div>}</section>;
}

function ToneCard({ art }: { art: Artwork }) {
  const [selected, setSelected] = useState<"weighted_color" | "physical">("weighted_color");
  const tone = art.sonification[selected];
  return <section className="tone-card"><div className="tone-top"><div><p className="eyebrow">Sonification</p><h2>The artwork as tone</h2></div>{tone.available && <div className="note-display"><strong>{tone.note}{tone.octave}</strong><span>{tone.frequency_hz?.toFixed(2)} Hz</span></div>}</div><div className="tone-tabs"><button className={selected === "weighted_color" ? "active" : ""} onClick={() => setSelected("weighted_color")}>Color tone</button><button disabled={!art.sonification.physical.available} className={selected === "physical" ? "active" : ""} onClick={() => setSelected("physical")}>Physical tone</button></div>{tone.available ? <><div className="audio-actions"><button className="play-button" onClick={() => playTone(tone)}><Play fill="currentColor" /> Play tone</button><button className="icon-button" aria-label="Stop audio" onClick={stopAudio}><Pause /></button><button className="outline-button" onClick={() => playArpeggio(art.sonification.palette_arpeggio.notes)}><Play size={16} /> Play palette</button></div><div className="why"><strong>Why this sound?</strong><p>{tone.explanation?.pitch}. {tone.explanation?.register}.</p></div></> : <p className="unavailable">{tone.reason}</p>}</section>;
}

function ArtworkPage() {
  const { id = "" } = useParams(); const [art, setArt] = useState<Artwork>(); const [error, setError] = useState("");
  useEffect(() => { stopAudio(); setArt(undefined); api.artwork(id).then(setArt).catch((e) => setError(String(e))); return stopAudio; }, [id]);
  if (error) return <Shell><main className="message">{error}</main></Shell>;
  if (!art) return <Shell><Loading label="Opening artwork" /></Shell>;
  const f = art.weighted_features;
  return <Shell><main className="artwork-page"><Link className="back" to="/"><ChevronLeft /> Back to collection</Link><section className="artwork-hero"><div className="artwork-image-stage"><img src={art.image_thumbnail || art.image_native} alt={`${art.display_title} by ${art.artist_display || "unknown artist"}`} /></div><div className="artwork-info"><p className="eyebrow">{art.classification || "Artwork"} · {art.object_number}</p><h1>{art.display_title}</h1><p className="artwork-byline">{art.artist_display || "Unknown artist"}</p><p className="muted">{art.date_text}{art.net_width_cm ? ` · ${art.net_width_cm} × ${art.net_height_cm} cm` : ""}</p><div className="feature-pills"><span>L {Number(f.centroid_l).toFixed(3)}</span><span>C {Number(f.centroid_chroma).toFixed(3)}</span><span>spread {Number(f.palette_spread_oklab).toFixed(3)}</span></div><PaletteBar palette={art.weighted_palette} /></div></section><ToneCard art={art} /><SimilarWorks id={id} /><section className="provenance"><p className="eyebrow">What comes from where</p><div>{Object.entries(art.provenance).map(([key, value]) => <p key={key}><strong>{key.replaceAll("_", " ")}</strong>{value}</p>)}</div></section></main></Shell>;
}

function About() { return <Shell><main className="about"><p className="kicker"><Sparkles size={14} /> About the experiment</p><h1>Colour is data.<br /><em>Sound is interpretation.</em></h1><div className="about-grid"><p>SMK Playground uses open collection metadata and images from Statens Museum for Kunst. The corpus contains public-domain works with usable image and palette data.</p><p>Palette weights come from SMK’s enrichment data. Perceptual colour features, similarity distances and sonification parameters are derived here and versioned separately.</p><p>Hue-to-pitch and size-to-register are deterministic artistic conventions—not natural laws or claims about how paintings “really” sound.</p></div></main></Shell> }

export default function App() { return <Routes><Route path="/" element={<Home />} /><Route path="/artwork/:id" element={<ArtworkPage />} /><Route path="/about" element={<About />} /></Routes>; }
