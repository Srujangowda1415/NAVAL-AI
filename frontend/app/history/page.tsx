"use client";

import { useEffect, useState } from "react";
import { Trash2, FileDown, Image as ImageIcon, Video as VideoIcon } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { HistoryItem } from "@/lib/types";
import BracketPanel from "@/components/BracketPanel";
import StatusBadge from "@/components/StatusBadge";

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = () => {
    api
      .history()
      .then(setItems)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Could not reach the backend."));
  };

  useEffect(load, []);

  // If any video job is still queued/processing, poll so status updates
  // without a manual refresh — this is where a background-worker video
  // upload shows up while it finishes.
  useEffect(() => {
    if (!items?.some((i) => i.status === "pending" || i.status === "processing")) return;
    const timer = setInterval(load, 4000);
    return () => clearInterval(timer);
  }, [items]);

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      await api.deleteHistoryItem(id);
      setItems((prev) => prev?.filter((i) => i.id !== id) ?? null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Delete failed.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="font-display text-3xl font-semibold">Detection History</h1>
      <p className="mt-1 font-data text-xs uppercase tracking-widest text-mist">
        Every image and video processed by the system
      </p>

      {error && <BracketPanel className="mt-8 border-hazardous/50 text-hazardous">{error}</BracketPanel>}

      {items && items.length === 0 && (
        <BracketPanel className="mt-8 text-center text-mist">No detection jobs yet.</BracketPanel>
      )}

      {items && items.length > 0 && (
        <BracketPanel className="mt-8 !p-0">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-navy-border font-data text-xs uppercase tracking-widest text-mist">
                <th className="px-6 py-3">File</th>
                <th className="px-6 py-3">Type</th>
                <th className="px-6 py-3">Ships</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((job) => (
                <tr key={job.id} className="border-b border-navy-border/50 last:border-0">
                  <td className="px-6 py-3 font-medium">{job.filename}</td>
                  <td className="px-6 py-3 text-mist">
                    <span className="inline-flex items-center gap-1.5">
                      {job.media_type === "image" ? <ImageIcon size={14} /> : <VideoIcon size={14} />}
                      {job.media_type}
                    </span>
                  </td>
                  <td className="px-6 py-3 font-data">{job.total_ships}</td>
                  <td className="px-6 py-3">
                    <StatusBadge status={job.status} hazardousCount={job.hazardous_count} />
                  </td>
                  <td className="px-6 py-3 font-data text-xs text-mist">
                    {new Date(job.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-3">
                    <div className="flex items-center justify-end gap-3">
                      {job.status === "completed" && (
                        <a
                          href={api.reportUrl(job.id)}
                          title="Download PDF report"
                          className="text-steel-bright hover:text-white"
                        >
                          <FileDown size={16} />
                        </a>
                      )}
                      <button
                        onClick={() => handleDelete(job.id)}
                        disabled={deletingId === job.id}
                        title="Delete"
                        className="text-mist hover:text-hazardous disabled:opacity-50"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </BracketPanel>
      )}
    </div>
  );
}
