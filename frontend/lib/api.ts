import type {
  AuthToken,
  DetectionResponse,
  HealthResponse,
  HistoryItem,
  JobAcceptedResponse,
  Role,
  User,
} from "./types";

// Configure at build/deploy time via .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000/api
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

// The backend serves annotated media/reports as relative paths (/outputs/...,
// /reports/...); resolve those against the API's origin, not /api itself.
const API_ORIGIN = API_BASE.replace(/\/api\/?$/, "");

export function resolveMediaUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${API_ORIGIN}${path}`;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// --- Token storage --------------------------------------------------------
// A plain module-level variable, not React state — lib/api.ts isn't a
// component and shouldn't need to be. lib/auth.tsx (the AuthProvider) is
// the source of truth for React re-renders; this is just what request()
// reads to attach the Authorization header. Persisted to localStorage so
// a page refresh doesn't log the user out.

const TOKEN_STORAGE_KEY = "naval-ai-token";
let currentToken: string | null = null;

export function setAuthToken(token: string | null) {
  currentToken = token;
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function loadStoredAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  currentToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  return currentToken;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (currentToken) headers.set("Authorization", `Bearer ${currentToken}`);

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  uploadImage: (file: File, model: "standard" | "all_weather" = "standard") => {
    const form = new FormData();
    form.append("file", file);
    return request<DetectionResponse>(`/upload-image?model=${model}`, { method: "POST", body: form });
  },

  uploadVideo: (file: File, model: "standard" | "all_weather" = "standard") => {
    const form = new FormData();
    form.append("file", file);
    // Videos are processed asynchronously — this returns as soon as the job
    // is queued (202 Accepted), not once detection is done. Poll getJob().
    return request<JobAcceptedResponse>(`/upload-video?model=${model}`, { method: "POST", body: form });
  },

  getJob: (id: number) => request<DetectionResponse>(`/jobs/${id}`),

  history: () => request<HistoryItem[]>("/history"),

  deleteHistoryItem: (id: number) => request<{ deleted: number }>(`/history/${id}`, { method: "DELETE" }),

  reportUrl: (id: number) => `${API_BASE}/report/${id}`,

  // --- Auth ---
  register: (email: string, password: string) =>
    request<User>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),

  login: async (email: string, password: string): Promise<AuthToken> => {
    // The backend uses FastAPI's standard OAuth2PasswordRequestForm, which
    // expects form-encoded fields (not JSON) with the email in "username".
    const body = new URLSearchParams({ username: email, password });
    return request<AuthToken>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  },

  me: () => request<User>("/auth/me"),

  listUsers: () => request<User[]>("/auth/users"),

  updateUserRole: (id: number, role: Role) =>
    request<User>(`/auth/users/${id}/role`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    }),
};

/**
 * Polls GET /jobs/{id} until status is "completed" or "failed".
 * Used for video uploads, which are processed asynchronously by a
 * background worker (see backend/worker.py) — see UploadPage.
 */
export async function pollJobUntilDone(
  id: number,
  { intervalMs = 2000, timeoutMs = 20 * 60 * 1000 }: { intervalMs?: number; timeoutMs?: number } = {},
): Promise<DetectionResponse> {
  const start = Date.now();
  while (true) {
    const job = await api.getJob(id);
    if (job.status === "completed" || job.status === "failed") return job;
    if (Date.now() - start > timeoutMs) {
      throw new ApiError(`Job ${id} did not finish within ${Math.round(timeoutMs / 1000)}s`, 408);
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

export { ApiError };
