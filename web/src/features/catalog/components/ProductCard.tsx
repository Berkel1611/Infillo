import { Package01Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import Link from "next/link";

import { formatPrice } from "../availability";
import type { ProductRow } from "../types";
import { AvailabilityBadge } from "./AvailabilityBadge";

/** A card for a list. The whole card is clickable through the stretched link of its heading. */
export function ProductCard({ product }: { product: ProductRow }) {
  return (
    <li className="relative flex flex-col overflow-hidden rounded-2xl border bg-card text-card-foreground has-focus-visible:ring-3 has-focus-visible:ring-ring/50">
      {/* Product photos arrive in stage 4; until then a neutral placeholder */}
      <div
        aria-hidden
        className="grid aspect-4/3 place-items-center bg-muted text-muted-foreground"
      >
        <HugeiconsIcon icon={Package01Icon} className="size-12" />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <h2 className="font-medium">
          <Link
            href={`/products/${product.id}`}
            className="outline-none after:absolute after:inset-0 hover:underline"
          >
            {product.name}
          </Link>
        </h2>
        <p className="text-sm text-muted-foreground">{product.category.name}</p>
        <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-2">
          <span className="font-semibold">
            {product.price_from
              ? `od ${formatPrice(product.price_from)}`
              : "Brak ceny"}
          </span>
          <AvailabilityBadge availability={product.availability} />
        </div>
      </div>
    </li>
  );
}
