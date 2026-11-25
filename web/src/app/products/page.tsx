import type { Metadata } from "next";
import { Suspense } from "react";

import { ProductList } from "@/features/catalog/components/ProductList";
import { PageSpinner } from "@/shared/layout/page-states";

export const metadata: Metadata = { title: "Produkty" };

export default function ProductsPage() {
  // useSearchParams needs a Suspense boundary: the shell is prerendered, the list is not
  return (
    <Suspense fallback={<PageSpinner />}>
      <ProductList />
    </Suspense>
  );
}
