import { api } from "@/shared/api/client";

export type HealthResponse = {
  status: string;
  database: "ok" | "error";
};

export function getHealth() {
  return api.get<HealthResponse>("/health");
}
