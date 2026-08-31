import type { LucideIcon } from "lucide-react";
import BracketPanel from "./BracketPanel";

export default function StatCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: "steel" | "safe" | "hazardous" | "suspicious";
}) {
  const accentClass = {
    steel: "text-steel-bright",
    safe: "text-safe",
    hazardous: "text-hazardous",
    suspicious: "text-suspicious",
  }[accent ?? "steel"];

  return (
    <BracketPanel className="flex items-center justify-between">
      <div>
        <p className="font-data text-xs uppercase tracking-widest text-mist">{label}</p>
        <p className="mt-2 font-display text-3xl font-semibold">{value}</p>
      </div>
      <Icon size={28} className={accentClass} aria-hidden />
    </BracketPanel>
  );
}
