"use client";

import { useState } from "react";
import clsx from "clsx";
import { Ship, ShieldAlert, Clock, Percent, Loader2 } from "lucide-react";
import UploadDropzone from "@/components/UploadDropzone";
import DetectionTable from "@/components/DetectionTable";
import BracketPanel from "@/components/BracketPanel";
import StatCard from "@/components/StatCard";
import { api, ApiError, pollJobUntilDone, resolveMediaUrl } from "@/lib/api";
import type { DetectionResponse } from "@/lib/types";

import { CloudSun, Eye } from "lucide-react";

type Mode = "image" | "video";
type ModelVariant = "standard" | "all_weather";

export default function UploadPage() {
  const [mode, setMode] = useState<Mode>("image");
  const [modelVariant, setModelVariant] = useState<ModelVariant>("standard");
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResponse | null>(null);

  const handleFile = async (file: File) => {
    setUploading(true);
    setError(null);
    setResult(null);

    try {
      if (mode === "image") {
        // Images process synchronously — the response already has full results.
        const response = await api.uploadImage(file, modelVariant);
        setResult(response);
      } else {
        // Videos are queued and processed by a background worker so a long
        // upload doesn't block the request — poll until it's done.
        const accepted = await api.uploadVideo(file, modelVariant);
        setStatusMessage("Queued — waiting for a worker to pick up the job…");
        const finished = await pollJobUntilDone(accepted.id, {
          intervalMs: 2000,
        });
        if (finished.status === "failed") {
          setError(finished.error_message ?? "Video processing failed.");
        } else {
          setResult(finished);
        }
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Upload failed — check that the backend is reachable.");
    } finally {
      setUploading(false);
      setStatusMessage(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <h1 className="font-display text-3xl font-semibold">Run a Detection</h1>
      <p className="mt-1 font-data text-xs uppercase tracking-widest text-mist">
        Upload an image or video for ship detection and hazard scoring
      </p>

      <div className="mt-8 flex flex-wrap items-start gap-6">
        {/* Media type selector */}
        <div>
          <p className="mb-2 font-data text-[10px] uppercase tracking-widest text-mist">Media type</p>
          <div className="flex gap-2">
            {(["image", "video"] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m);
                  setResult(null);
                  setError(null);
                }}
                className={clsx(
                  "rounded-sm border px-4 py-2 font-data text-xs uppercase tracking-wide transition-colors",
                  mode === m
                    ? "border-steel-bright bg-navy-light text-steel-bright"
                    : "border-navy-border text-mist hover:text-white",
                )}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        {/* Model selector */}
        <div>
          <p className="mb-2 font-data text-[10px] uppercase tracking-widest text-mist">Detection model</p>
          <div className="flex gap-2">
            <button
              id="model-standard"
              onClick={() => setModelVariant("standard")}
              className={clsx(
                "flex items-center gap-2 rounded-sm border px-4 py-2 font-data text-xs uppercase tracking-wide transition-colors",
                modelVariant === "standard"
                  ? "border-steel-bright bg-navy-light text-steel-bright"
                  : "border-navy-border text-mist hover:text-white",
              )}
              title="Standard model — best accuracy in clear conditions"
            >
              <Eye size={13} />
              Standard
            </button>
            <button
              id="model-all-weather"
              onClick={() => setModelVariant("all_weather")}
              className={clsx(
                "flex items-center gap-2 rounded-sm border px-4 py-2 font-data text-xs uppercase tracking-wide transition-colors",
                modelVariant === "all_weather"
                  ? "border-steel-bright bg-navy-light text-steel-bright"
                  : "border-navy-border text-mist hover:text-white",
              )}
              title="All-Weather model — handles fog, rain, blur, and low-visibility images"
            >
              <CloudSun size={13} />
              All-Weather
            </button>
          </div>
          {modelVariant === "all_weather" && (
            <p className="mt-1.5 font-data text-[10px] text-steel-bright">
              ⛅ All-Weather mode active — lower confidence threshold for degraded / blurry images
            </p>
          )}
        </div>
      </div>

      <div className="mt-4">
        <UploadDropzone
          accept={mode === "image" ? "image/jpeg,image/png,image/bmp" : "video/mp4,video/x-msvideo,video/quicktime"}
          label={mode === "image" ? "Drop an image, or click to browse" : "Drop a video, or click to browse"}
          hint={mode === "image" ? "JPG, PNG, BMP" : "MP4, AVI, MOV — processed in the background, may take a while"}
          uploading={uploading}
          onFileSelected={handleFile}
        />
      </div>

      {uploading && mode === "video" && (
        <BracketPanel className="mt-6 flex items-center gap-3 text-mist">
          <Loader2 size={18} className="animate-spin text-steel-bright" aria-hidden />
          <span className="font-data text-sm">
            {statusMessage ?? "Processing…"} This page will update automatically — feel free to check{" "}
            <a href="/history" className="text-steel-bright hover:underline">History</a> later instead of waiting.
          </span>
        </BracketPanel>
      )}

      {error && (
        <BracketPanel className="mt-6 border-hazardous/50 text-hazardous">{error}</BracketPanel>
      )}

      {result && (
        <div className="mt-8 space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Ships Found" value={result.total_ships} icon={Ship} accent="steel" />
            <StatCard label="Hazardous" value={result.hazardous_count} icon={ShieldAlert} accent="hazardous" />
            <StatCard label="Avg Confidence" value={`${(result.average_confidence * 100).toFixed(0)}%`} icon={Percent} accent="safe" />
            <StatCard label="Processing Time" value={`${result.processing_time_seconds.toFixed(2)}s`} icon={Clock} accent="steel" />
          </div>

          {result.annotated_output_url && (
            <BracketPanel>
              <h2 className="font-display text-lg font-semibold">Annotated output</h2>
              <div className="mt-4 overflow-hidden rounded-sm border border-navy-border">
                {result.media_type === "image" ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={resolveMediaUrl(result.annotated_output_url)} alt="Annotated detection result" className="w-full" />
                ) : (
                  <video src={resolveMediaUrl(result.annotated_output_url)} controls className="w-full" />
                )}
              </div>
            </BracketPanel>
          )}

          <BracketPanel>
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold">Detected ships</h2>
              <a
                href={api.reportUrl(result.id)}
                className="font-data text-xs text-steel-bright hover:underline"
              >
                Download PDF report →
              </a>
            </div>
            <div className="mt-4">
              <DetectionTable detections={result.detections} />
            </div>
          </BracketPanel>
        </div>
      )}
    </div>
  );
}
