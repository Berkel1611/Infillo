"use client";

import { LockIcon } from "@hugeicons/core-free-icons";
import Link from "next/link";
import type { ReactNode } from "react";

import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { useCurrentUser } from "../hooks";
import type { UserRole } from "../types";

/** Used inside AuthGuard: shows the page only to the given roles. The API checks them too. */
export function RoleGate({
  roles,
  children,
}: {
  roles: UserRole[];
  children: ReactNode;
}) {
  const { data: user } = useCurrentUser();

  if (!user) {
    return null; // AuthGuard above handles loading and guests
  }
  if (!roles.includes(user.role)) {
    return (
      <PageMessage
        icon={LockIcon}
        title="Brak dostępu"
        description="Nie masz uprawnień do tej strony."
        action={
          <Button render={<Link href="/" />} nativeButton={false}>
            Wróć na stronę główną
          </Button>
        }
      />
    );
  }
  return children;
}
