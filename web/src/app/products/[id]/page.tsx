import type { Metadata } from "next";
import { Suspense } from "react";

import { ProductDetail } from "@/features/catalog/components/ProductDetail";
import { PageSpinner } from "@/shared/layout/page-states";

export const metadata: Metadata = { title: "Produkt" };

export default function ProductPage() {
  // The id comes from the address and is read in the client component (useParams),
  // so the page shell stays static and the product loads in the browser
  return (
    <Suspense fallback={<PageSpinner />}>
      <ProductDetail />
    </Suspense>
  );
}
