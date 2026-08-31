"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud, Loader2 } from "lucide-react";
import clsx from "clsx";

export default function UploadDropzone({
  accept,
  label,
  hint,
  uploading,
  onFileSelected,
}: {
  accept: string;
  label: string;
  hint: string;
  uploading: boolean;
  onFileSelected: (file: File) => void;
}) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      onFileSelected(files[0]);
    },
    [onFileSelected],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={label}
      onClick={() => !uploading && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !uploading) inputRef.current?.click();
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        if (!uploading) handleFiles(e.dataTransfer.files);
      }}
      className={clsx(
        "bracket-panel flex cursor-pointer flex-col items-center justify-center gap-3 border-dashed px-6 py-16 text-center transition-colors",
        dragOver && "bg-navy-light",
        uploading && "cursor-not-allowed opacity-70",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        disabled={uploading}
        onChange={(e) => handleFiles(e.target.files)}
      />
      {uploading ? (
        <Loader2 size={32} className="animate-spin text-steel-bright" aria-hidden />
      ) : (
        <UploadCloud size={32} className="text-steel-bright" aria-hidden />
      )}
      <p className="font-display text-lg font-medium">
        {uploading ? "Processing detection…" : label}
      </p>
      {!uploading && <p className="font-data text-xs text-mist">{hint}</p>}
    </div>
  );
}
