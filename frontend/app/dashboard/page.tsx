"use client";

import { useEffect, useMemo, useState } from "react";
import { Ship, ShieldAlert, ShieldCheck, Gauge } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ApiError } from "@/lib/api";
import type { HistoryItem } from "@/lib/types";
import StatCard from "@/components/StatCard";
import BracketPanel from "@/components/BracketPanel";
import HazardBadge from "@/components/HazardBadge";
import Link from "next/link";

export default function DashboardPage() {
  const [history, setHistory] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .history()
      .then(setHistory)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Could not reach the backend."));
  }, []);

  const stats = useMemo(() => {
    if (!history) return null;
    const totalShips = history.reduce((sum, j) => sum + j.total_ships, 0);
    const hazardous = history.reduce((sum, j) => sum + j.hazardous_count, 0);
    const images = history.filter((j) => j.media_type === "image").length;
    const videos = history.filter((j) => j.media_type === "video").length;
    return { totalShips, hazardous, images, videos, jobs: history.length };
  }, [history]);

  const chartData = useMemo(() => {
    if (!history) return [];
    return history
      .slice(0, 10)
      .reverse()
      .map((j) => ({ name: j.filename.slice(0, 14), ships: j.total_ships, hazardous: j.hazardous_count }));
  }, [history]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <h1 className="font-display text-3xl font-semibold">Dashboard</h1>
      <p className="mt-1 font-data text-xs uppercase tracking-widest text-mist">
        Fleet-wide detection overview
      </p>

      {error && (
        <BracketPanel className="mt-8 border-hazardous/50 text-hazardous">
          Could not load detection history: {error}. Confirm the backend is running and
          NEXT_PUBLIC_API_URL is set correctly.
        </BracketPanel>
      )}

      {stats && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Jobs" value={stats.jobs} icon={Gauge} accent="steel" />
          <StatCard label="Ships Detected" value={stats.totalShips} icon={Ship} accent="steel" />
          <StatCard label="Hazardous Ships" value={stats.hazardous} icon={ShieldAlert} accent="hazardous" />
          <StatCard label="Images / Videos" value={`${stats.images} / ${stats.videos}`} icon={ShieldCheck} accent="safe" />
        </div>
      )}

      {chartData.length > 0 && (
        <BracketPanel className="mt-6">
          <h2 className="font-display text-lg font-semibold">Ships per recent upload</h2>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid stroke="var(--color-navy-border)" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: "var(--color-mist)", fontSize: 11 }} />
                <YAxis tick={{ fill: "var(--color-mist)", fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: "var(--color-navy)", border: "1px solid var(--color-navy-border)" }}
                  labelStyle={{ color: "var(--color-white)" }}
                />
                <Bar dataKey="ships" fill="var(--color-steel)" radius={[2, 2, 0, 0]} name="Total ships" />
                <Bar dataKey="hazardous" fill="var(--color-hazardous)" radius={[2, 2, 0, 0]} name="Hazardous" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </BracketPanel>
      )}

      <BracketPanel className="mt-6">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold">Recent uploads</h2>
          <Link href="/history" className="font-data text-xs text-steel-bright hover:underline">
            View all →
          </Link>
        </div>
        {history && history.length === 0 && (
          <p className="mt-6 text-center font-data text-sm text-mist">
            No detections yet. <Link href="/upload" className="text-steel-bright hover:underline">Run your first upload</Link>.
          </p>
        )}
        {history && history.length > 0 && (
          <div className="mt-4 divide-y divide-navy-border/50">
            {history.slice(0, 6).map((job) => (
              <div key={job.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium">{job.filename}</p>
                  <p className="font-data text-xs text-mist">
                    {job.total_ships} ship{job.total_ships === 1 ? "" : "s"} · {new Date(job.created_at).toLocaleString()}
                  </p>
                </div>
                {job.hazardous_count > 0 ? <HazardBadge level="hazardous" /> : <HazardBadge level="safe" />}
              </div>
            ))}
          </div>
        )}
      </BracketPanel>
    </div>
  );
}
