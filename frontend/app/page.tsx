import Link from "next/link";
import { Ship, Video, ShieldAlert, FileDown, ArrowRight } from "lucide-react";
import BracketPanel from "@/components/BracketPanel";

const FEATURES = [
  {
    icon: Ship,
    title: "Detect & classify",
    body: "YOLO-based detection identifies every ship in an image or video and classifies it across 20 vessel types, from fishing boats to aircraft carriers.",
  },
  {
    icon: ShieldAlert,
    title: "Hazard scoring",
    body: "Every detection is scored Safe, Suspicious, Hazardous, or Unknown against a configurable rule set — no hardcoded logic, easy to audit and adjust.",
  },
  {
    icon: Video,
    title: "Video tracking",
    body: "ByteTrack/BoT-SORT tracking follows each ship across frames, collapsing hundreds of sightings into one summary per vessel.",
  },
  {
    icon: FileDown,
    title: "Reports on demand",
    body: "Every job — image or video — generates a downloadable PDF report with annotated output and full detection detail.",
  },
];

export default function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="grid-texture relative overflow-hidden border-b border-navy-border px-6 py-24">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-8 text-center">
          <div className="relative flex h-40 w-40 items-center justify-center">
            <svg viewBox="0 0 160 160" className="absolute inset-0 h-full w-full" aria-hidden>
              <circle cx="80" cy="80" r="78" fill="none" stroke="var(--color-navy-border)" strokeWidth="1" />
              <circle cx="80" cy="80" r="54" fill="none" stroke="var(--color-navy-border)" strokeWidth="1" />
              <circle cx="80" cy="80" r="28" fill="none" stroke="var(--color-navy-border)" strokeWidth="1" />
            </svg>
            <svg viewBox="0 0 160 160" className="radar-sweep absolute inset-0 h-full w-full" aria-hidden>
              <defs>
                <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="var(--color-steel-bright)" stopOpacity="0" />
                  <stop offset="100%" stopColor="var(--color-steel-bright)" stopOpacity="0.55" />
                </linearGradient>
              </defs>
              <path d="M80 80 L80 2 A78 78 0 0 1 149 55 Z" fill="url(#sweep)" />
            </svg>
            <Ship size={40} className="relative text-steel-bright" aria-hidden />
          </div>

          <h1 className="font-display text-5xl font-semibold tracking-tight md:text-6xl">
            NAVAL VESSEL DETECTION
            <span className="block text-steel-bright">&amp; CLASSIFICATION</span>
          </h1>
          <p className="max-w-2xl text-lg text-mist">
            Upload an image or video. The system finds every ship, classifies its type, and flags hazard
            status — with a full audit trail and a downloadable report for each job.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/upload"
              className="flex items-center gap-2 rounded-sm bg-steel px-6 py-3 font-data text-sm tracking-wide text-white transition-colors hover:bg-steel-bright"
            >
              Run a detection <ArrowRight size={16} aria-hidden />
            </Link>
            <Link
              href="/dashboard"
              className="rounded-sm border border-navy-border px-6 py-3 font-data text-sm tracking-wide text-mist transition-colors hover:border-steel-bright hover:text-white"
            >
              View dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <BracketPanel key={title}>
              <Icon size={24} className="text-steel-bright" aria-hidden />
              <h2 className="mt-4 font-display text-lg font-semibold">{title}</h2>
              <p className="mt-2 text-sm text-mist">{body}</p>
            </BracketPanel>
          ))}
        </div>
      </section>
    </div>
  );
}
