"use client";

import { useQuery } from "@tanstack/react-query";

import { getHealth } from "../api";

export function BackendStatus() {
  const { data, isPending, isError } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
  });

  if (isPending) {
    return <p role="status">Sprawdzam połączenie z serwerem…</p>;
  }
  if (isError) {
    return <p role="status">Serwer nie odpowiada.</p>;
  }
  return (
    <p role="status">
      Serwer działa. Baza danych:{" "}
      {data.database === "ok" ? "połączona" : "błąd połączenia"}.
    </p>
  );
}
