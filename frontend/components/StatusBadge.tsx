import { Loader2, Clock } from "lucide-react";
import type { JobStatus } from "@/lib/types";
import HazardBadge from "./HazardBadge";

/**
 * Shows job progress (pending/processing/failed) while a video is still
 * being worked on, and falls back to the usual hazard badge once a job
 * has actually completed and hazard levels are known.
 */
export default function StatusBadge({ status, hazardousCount }: { status: JobStatus; hazardousCount: number }) {
  if (status === "pending") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-sm bg-unknown/15 px-2 py-0.5 font-data text-xs tracking-wider text-unknown">
        <Clock size={12} aria-hidden /> QUEUED
      </span>
    );
  }
  if (status === "processing") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-sm bg-steel/15 px-2 py-0.5 font-data text-xs tracking-wider text-steel-bright">
        <Loader2 size={12} className="animate-spin" aria-hidden /> PROCESSING
      </span>
    );
  }
  if (status === "failed") {
    return <HazardBadge level="unknown" />;
  }
  return hazardousCount > 0 ? <HazardBadge level="hazardous" /> : <HazardBadge level="safe" />;
}
