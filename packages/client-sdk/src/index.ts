/**
 * @workoutbuddy/client-sdk
 *
 * Auto-generated TypeScript API client from the WorkoutBuddy FastAPI backend.
 * Run `pnpm generate:client` from the repo root to regenerate after the API is running.
 *
 * This file is a placeholder — it will be replaced by the generated OpenAPI client.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Placeholder types (will be replaced by generated types) ─────────────────

export type ApiResponse<T> = {
  data: T;
  status: number;
};

/** Health-check response shape mirroring the FastAPI /health endpoint */
export type HealthResponse = {
  status: "ok" | "degraded";
};
