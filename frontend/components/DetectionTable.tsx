import type { DetectionItem } from "@/lib/types";
import HazardBadge from "./HazardBadge";

export default function DetectionTable({ detections }: { detections: DetectionItem[] }) {
  if (detections.length === 0) {
    return (
      <p className="py-8 text-center font-data text-sm text-mist">No ships detected in this upload.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-navy-border font-data text-xs uppercase tracking-widest text-mist">
            <th className="py-2 pr-4">Track</th>
            <th className="py-2 pr-4">Ship Class</th>
            <th className="py-2 pr-4">Confidence</th>
            <th className="py-2 pr-4">Hazard</th>
            <th className="py-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          {detections.map((d, i) => (
            <tr key={i} className="border-b border-navy-border/50 last:border-0">
              <td className="py-3 pr-4 font-data text-mist">{d.track_id !== null ? `#${d.track_id}` : "—"}</td>
              <td className="py-3 pr-4 font-medium capitalize">{d.ship_class.replace(/_/g, " ")}</td>
              <td className="py-3 pr-4 font-data text-steel-bright">{(d.confidence * 100).toFixed(1)}%</td>
              <td className="py-3 pr-4">
                <HazardBadge level={d.hazard_level} />
              </td>
              <td className="py-3 text-mist">{d.hazard_reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
