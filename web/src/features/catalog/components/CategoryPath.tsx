import Link from "next/link";

import type { CategoryRef } from "../types";
import { productsHref } from "../urls";

/** Simple category trail of a product (full breadcrumbs come in stage 10). */
export function CategoryPath({ path }: { path: CategoryRef[] }) {
  return (
    <nav aria-label="Ścieżka kategorii">
      <ol className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
        <li>
          <Link
            href={productsHref()}
            className="underline-offset-4 hover:underline"
          >
            Produkty
          </Link>
        </li>
        {path.map((category) => (
          <li key={category.id} className="flex items-center gap-2">
            <span aria-hidden>/</span>
            <Link
              href={productsHref({ category: category.id })}
              className="underline-offset-4 hover:underline"
            >
              {category.name}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}
