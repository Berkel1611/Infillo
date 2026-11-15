import type { ReactNode } from "react";

import { AuthGuard } from "@/features/auth/components/AuthGuard";

export default function AppLayout({ children }: { children: ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}
