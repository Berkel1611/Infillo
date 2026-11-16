import type { Metadata } from "next";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { UsersPage } from "@/features/users/components/UsersPage";

export const metadata: Metadata = { title: "Użytkownicy" };

export default function AdminUsersPage() {
  return (
    <RoleGate roles={["admin"]}>
      <UsersPage />
    </RoleGate>
  );
}
