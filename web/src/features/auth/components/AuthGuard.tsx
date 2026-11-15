"use client";

import { CloudAlertIcon } from "@hugeicons/core-free-icons";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { useCurrentUser } from "../hooks";
import { withNext } from "../redirect";

/** Pages for logged-in users: a guest is sent to /login and brought back afterwards. */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: user, isError, isPending, refetch } = useCurrentUser();

  useEffect(() => {
    if (user === null) {
      router.replace(withNext("/login", pathname));
    }
  }, [user, pathname, router]);

  if (isError) {
    return (
      <PageMessage
        icon={CloudAlertIcon}
        title="Brak połączenia z serwerem"
        description="Sprawdź połączenie z internetem i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }
  if (isPending || user === null) {
    return <PageSpinner />;
  }
  return children;
}
