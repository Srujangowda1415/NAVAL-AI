"use client";

import { useEffect, useState } from "react";
import { FileText, Download } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { HistoryItem } from "@/lib/types";
import BracketPanel from "@/components/BracketPanel";
import HazardBadge from "@/components/HazardBadge";

export default function ReportsPage() {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .history()
      .then(setItems)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Could not reach the backend."));
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="font-display text-3xl font-semibold">Reports</h1>
      <p className="mt-1 font-data text-xs uppercase tracking-widest text-mist">
        Download a full PDF detection report for any completed job
      </p>

      {error && <BracketPanel className="mt-8 border-hazardous/50 text-hazardous">{error}</BracketPanel>}

      {items && items.filter((j) => j.status === "completed").length === 0 && (
        <BracketPanel className="mt-8 text-center text-mist">
          No completed jobs yet — reports appear here once a detection finishes.
        </BracketPanel>
      )}

      {items && items.filter((j) => j.status === "completed").length > 0 && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items
            .filter((j) => j.status === "completed")
            .map((job) => (
            <BracketPanel key={job.id} className="flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between">
                  <FileText size={22} className="text-steel-bright" aria-hidden />
                  {job.hazardous_count > 0 ? <HazardBadge level="hazardous" /> : <HazardBadge level="safe" />}
                </div>
                <p className="mt-4 truncate font-medium">{job.filename}</p>
                <p className="mt-1 font-data text-xs text-mist">
                  {job.total_ships} ship{job.total_ships === 1 ? "" : "s"} · {new Date(job.created_at).toLocaleDateString()}
                </p>
              </div>
              <a
                href={api.reportUrl(job.id)}
                className="mt-6 flex items-center justify-center gap-2 rounded-sm border border-navy-border py-2 font-data text-xs uppercase tracking-wide text-mist transition-colors hover:border-steel-bright hover:text-white"
              >
                <Download size={14} aria-hidden /> Download PDF
              </a>
            </BracketPanel>
          ))}
        </div>
      )}
    </div>
  );
}
