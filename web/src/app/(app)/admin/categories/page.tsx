import type { Metadata } from "next";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { CategoriesAdminPage } from "@/features/categories-admin/components/CategoriesAdminPage";

export const metadata: Metadata = { title: "Kategorie" };

export default function AdminCategoriesPage() {
  return (
    <RoleGate roles={["admin"]}>
      <CategoriesAdminPage />
    </RoleGate>
  );
}
