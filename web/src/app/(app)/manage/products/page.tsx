import type { Metadata } from "next";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { ManagedProductsPage } from "@/features/manage-products/components/ManagedProductsPage";

export const metadata: Metadata = { title: "Moje produkty" };

export default function ManageProductsPage() {
  return (
    <RoleGate roles={["moderator", "admin"]}>
      <ManagedProductsPage />
    </RoleGate>
  );
}
