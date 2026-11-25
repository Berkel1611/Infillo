import type { Metadata } from "next";
import { Suspense } from "react";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { ProductFormPage } from "@/features/manage-products/components/ProductFormPage";
import { PageSpinner } from "@/shared/layout/page-states";

export const metadata: Metadata = { title: "Edycja produktu" };

export default function EditProductPage() {
  // The id is read in the client component (useParams), so the shell stays static
  return (
    <RoleGate roles={["moderator", "admin"]}>
      <Suspense fallback={<PageSpinner />}>
        <ProductFormPage mode="edit" />
      </Suspense>
    </RoleGate>
  );
}
