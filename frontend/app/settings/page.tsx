"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";
import BracketPanel from "@/components/BracketPanel";

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Could not reach the backend."));
  }, []);

  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="font-display text-3xl font-semibold">Settings</h1>
      <p className="mt-1 font-data text-xs uppercase tracking-widest text-mist">
        System configuration &amp; status
      </p>

      <BracketPanel className="mt-8">
        <h2 className="font-display text-lg font-semibold">Backend connection</h2>
        <dl className="mt-4 space-y-3 font-data text-sm">
          <div className="flex items-center justify-between border-b border-navy-border/50 pb-3">
            <dt className="text-mist">API endpoint</dt>
            <dd>{apiBase}</dd>
          </div>
          <div className="flex items-center justify-between border-b border-navy-border/50 pb-3">
            <dt className="text-mist">Status</dt>
            <dd>
              {!health && !error && <Loader2 size={16} className="animate-spin text-steel-bright" />}
              {health && (
                <span className="flex items-center gap-1.5 text-safe">
                  <CheckCircle2 size={16} /> {health.status} ({health.app_env})
                </span>
              )}
              {error && (
                <span className="flex items-center gap-1.5 text-hazardous">
                  <XCircle size={16} /> unreachable
                </span>
              )}
            </dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-mist">Model loaded</dt>
            <dd>
              {health?.model_loaded ? (
                <span className="flex items-center gap-1.5 text-safe">
                  <CheckCircle2 size={16} /> yes
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-suspicious">
                  <XCircle size={16} /> no — train a model (see backend/training/)
                </span>
              )}
            </dd>
          </div>
        </dl>
      </BracketPanel>

      <BracketPanel className="mt-6">
        <h2 className="font-display text-lg font-semibold">Configuration</h2>
        <p className="mt-3 text-sm text-mist">
          Detection thresholds, hazard rules, and video limits are configured server-side and intentionally
          not exposed here for editing — they live in version-controlled config files so every change is
          reviewable:
        </p>
        <ul className="mt-4 space-y-2 font-data text-xs text-mist">
          <li>
            <span className="text-steel-bright">backend/config/hazard_rules.yaml</span> — hazard level per ship class
          </li>
          <li>
            <span className="text-steel-bright">backend/.env</span> — confidence/IoU thresholds, video duration limit, device
          </li>
        </ul>
        <p className="mt-4 text-sm text-mist">
          To point this dashboard at a different backend, set{" "}
          <span className="font-data text-steel-bright">NEXT_PUBLIC_API_URL</span> in{" "}
          <span className="font-data text-steel-bright">frontend/.env.local</span> and restart the dev server.
        </p>
      </BracketPanel>
    </div>
  );
}
