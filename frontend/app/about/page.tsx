import { Ship, ShieldAlert, Video, Database, Layers } from "lucide-react";
import BracketPanel from "@/components/BracketPanel";

const STACK = [
  { label: "Detection", value: "Ultralytics YOLO, PyTorch, OpenCV" },
  { label: "Backend", value: "FastAPI, SQLAlchemy, PostgreSQL" },
  { label: "Frontend", value: "Next.js (App Router), TypeScript, Tailwind CSS" },
  { label: "Tracking", value: "ByteTrack / BoT-SORT" },
  { label: "Reports", value: "ReportLab (PDF)" },
];

const SHIP_CLASSES = [
  "Cargo Ship", "Oil Tanker", "Container Ship", "Bulk Carrier", "Passenger Ship",
  "Cruise Ship", "Fishing Vessel", "Patrol Boat", "Corvette", "Frigate",
  "Destroyer", "Aircraft Carrier", "Amphibious Assault Ship", "Landing Ship",
  "Submarine", "Tug Boat", "Support Vessel", "Yacht", "Sail Boat", "Coast Guard Vessel",
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="font-display text-3xl font-semibold">About This Project</h1>
      <p className="mt-4 text-mist">
        The Naval Vessel Detection &amp; Classification System detects ships in images and video, classifies
        their type across 20 vessel classes, and scores each one against a configurable hazard policy — Safe,
        Suspicious, Hazardous, or Unknown. It&apos;s built as a modular pipeline so future capabilities (live
        feeds, satellite imagery, AIS/radar fusion) can be added without reworking the core.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <BracketPanel>
          <Ship size={22} className="text-steel-bright" aria-hidden />
          <h2 className="mt-3 font-display text-lg font-semibold">20 vessel classes</h2>
          <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 font-data text-xs text-mist">
            {SHIP_CLASSES.map((c) => (
              <li key={c}>· {c}</li>
            ))}
          </ul>
        </BracketPanel>

        <div className="flex flex-col gap-4">
          <BracketPanel>
            <ShieldAlert size={22} className="text-steel-bright" aria-hidden />
            <h2 className="mt-3 font-display text-lg font-semibold">Hazard scoring</h2>
            <p className="mt-2 text-sm text-mist">
              Rule-based today, defined entirely in a config file — swappable for an ML-based classifier later
              without changing any calling code.
            </p>
          </BracketPanel>
          <BracketPanel>
            <Video size={22} className="text-steel-bright" aria-hidden />
            <h2 className="mt-3 font-display text-lg font-semibold">Video tracking</h2>
            <p className="mt-2 text-sm text-mist">
              Multi-object tracking follows each ship across frames so a single vessel isn&apos;t double-counted.
            </p>
          </BracketPanel>
        </div>
      </div>

      <BracketPanel className="mt-6">
        <div className="flex items-center gap-2">
          <Layers size={22} className="text-steel-bright" aria-hidden />
          <h2 className="font-display text-lg font-semibold">Technology stack</h2>
        </div>
        <dl className="mt-4 space-y-2">
          {STACK.map(({ label, value }) => (
            <div key={label} className="flex flex-col gap-0.5 border-b border-navy-border/50 pb-2 sm:flex-row sm:justify-between">
              <dt className="font-data text-xs uppercase tracking-widest text-mist">{label}</dt>
              <dd className="text-sm">{value}</dd>
            </div>
          ))}
        </dl>
      </BracketPanel>

      <BracketPanel className="mt-6">
        <div className="flex items-center gap-2">
          <Database size={22} className="text-steel-bright" aria-hidden />
          <h2 className="font-display text-lg font-semibold">Planned next</h2>
        </div>
        <p className="mt-2 text-sm text-mist">
          Live webcam/drone/satellite feeds, radar and AIS fusion, multi-camera tracking, real-time alerts,
          Docker/Kubernetes deployment, and role-based multi-user access.
        </p>
      </BracketPanel>
    </div>
  );
}
