"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { toast } from "sonner";

import { ApiError } from "@/shared/api/client";

import { currentUserKey } from "../hooks";

function isSessionLost(error: unknown): boolean {
  // INVALID_CREDENTIALS (wrong password) is also 401, but it is not a lost session
  return error instanceof ApiError && error.code === "NOT_AUTHENTICATED";
}

/**
 * When any request answers 401 NOT_AUTHENTICATED (session expired, account blocked),
 * forget the cached user: AuthGuard then sends protected pages to /login?next=...
 * and the header shows "Zaloguj się". Renders nothing.
 */
export function SessionExpiryListener() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const onError = (error: unknown) => {
      if (!isSessionLost(error) || !queryClient.getQueryData(currentUserKey)) {
        return; // not a lost session, or already shown as logged out
      }
      queryClient.setQueryData(currentUserKey, null);
      toast.info("Sesja wygasła. Zaloguj się ponownie.");
    };

    const unsubscribeQueries = queryClient
      .getQueryCache()
      .subscribe((event) => {
        if (event.type === "updated" && event.action.type === "error") {
          onError(event.action.error);
        }
      });
    const unsubscribeMutations = queryClient
      .getMutationCache()
      .subscribe((event) => {
        if (event.type === "updated" && event.action.type === "error") {
          onError(event.action.error);
        }
      });

    return () => {
      unsubscribeQueries();
      unsubscribeMutations();
    };
  }, [queryClient]);

  return null;
}
