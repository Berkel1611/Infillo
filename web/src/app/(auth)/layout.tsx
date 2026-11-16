import { type ReactNode, Suspense } from "react";

import { AuthBrandPanel } from "@/features/auth/components/AuthBrandPanel";
import { GuestGuard } from "@/features/auth/components/GuestGuard";
import { Spinner } from "@/shared/ui/spinner";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-8 lg:grid-cols-2 lg:gap-12 lg:py-12">
      <div className="flex items-center justify-center">
        <div className="w-full max-w-md">
          {/* GuestGuard and the forms read ?next= (useSearchParams): needs Suspense */}
          <Suspense
            fallback={
              <div className="flex justify-center py-10">
                <Spinner className="size-6" />
              </div>
            }
          >
            <GuestGuard>{children}</GuestGuard>
          </Suspense>
        </div>
      </div>
      <AuthBrandPanel />
    </div>
  );
}
