// Mirrors backend/api/schemas/detection.py — keep in sync manually since
// there's no shared schema generation step yet.

export type HazardLevel = "safe" | "suspicious" | "hazardous" | "unknown";
export type MediaType = "image" | "video";
export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface DetectionItem {
  ship_class: string;
  confidence: number;
  bbox_xyxy: [number, number, number, number];
  track_id: number | null;
  hazard_level: HazardLevel;
  hazard_reason: string;
}

export interface DetectionResponse {
  id: number;
  filename: string;
  media_type: MediaType;
  status: JobStatus;
  error_message: string | null;
  detections: DetectionItem[];
  total_ships: number;
  hazardous_count: number;
  average_confidence: number;
  processing_time_seconds: number;
  annotated_output_url: string | null;
  created_at: string;
}

export interface JobAcceptedResponse {
  id: number;
  filename: string;
  media_type: MediaType;
  status: JobStatus;
}

export interface HistoryItem {
  id: number;
  filename: string;
  media_type: MediaType;
  status: JobStatus;
  total_ships: number;
  hazardous_count: number;
  created_at: string;
}

export type Role = "viewer" | "analyst" | "admin";

export interface User {
  id: number;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  app_env: string;
}
