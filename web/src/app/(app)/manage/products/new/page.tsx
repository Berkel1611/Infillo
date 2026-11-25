import type { Metadata } from "next";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { ProductFormPage } from "@/features/manage-products/components/ProductFormPage";

export const metadata: Metadata = { title: "Nowy produkt" };

export default function NewProductPage() {
  return (
    <RoleGate roles={["moderator", "admin"]}>
      <ProductFormPage mode="new" />
    </RoleGate>
  );
}
