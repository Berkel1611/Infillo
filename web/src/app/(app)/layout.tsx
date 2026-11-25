import { type ReactNode, Suspense } from "react";

import { AuthGuard } from "@/features/auth/components/AuthGuard";
import { PageSpinner } from "@/shared/layout/page-states";

export default function AppLayout({ children }: { children: ReactNode }) {
  // AuthGuard reads the pathname, which is unknown at build time on routes with a dynamic
  // segment (e.g. /manage/products/[id]); Suspense lets the rest of the page be prerendered
  return (
    <Suspense fallback={<PageSpinner />}>
      <AuthGuard>{children}</AuthGuard>
    </Suspense>
  );
}
