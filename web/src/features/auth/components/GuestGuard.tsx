"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { Spinner } from "@/shared/ui/spinner";

import { useCurrentUser } from "../hooks";
import { safeNextPath } from "../redirect";

/** Login and registration are for guests: a logged-in user is sent on to ?next= (or "/"). */
export function GuestGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const destination = safeNextPath(useSearchParams().get("next"));
  const { data: user, isPending } = useCurrentUser();

  useEffect(() => {
    if (user) {
      router.replace(destination);
    }
  }, [user, destination, router]);
  if (isPending || user) {
    return (
      <div className="flex justify-center py-10">
        <Spinner className="size-6" />
      </div>
    );
  }
  return children;
}
