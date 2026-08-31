import type { HazardLevel } from "@/lib/types";

const HAZARD_STYLES: Record<HazardLevel, { bg: string; text: string; label: string }> = {
  safe: { bg: "bg-safe/15", text: "text-safe", label: "SAFE" },
  suspicious: { bg: "bg-suspicious/15", text: "text-suspicious", label: "SUSPICIOUS" },
  hazardous: { bg: "bg-hazardous/15", text: "text-hazardous", label: "HAZARDOUS" },
  unknown: { bg: "bg-unknown/15", text: "text-unknown", label: "UNKNOWN" },
};

export default function HazardBadge({ level }: { level: HazardLevel }) {
  const style = HAZARD_STYLES[level] ?? HAZARD_STYLES.unknown;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 font-data text-xs tracking-wider ${style.bg} ${style.text}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {style.label}
    </span>
  );
}
