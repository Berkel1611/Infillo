import Link from "next/link";

import { AvailabilityBadge } from "@/features/catalog/components/AvailabilityBadge";
import { formatPrice } from "@/features/catalog/availability";
import type { ManagedProductRow } from "@/features/catalog/types";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

/** The status is a word, not only a color: a draft is "Szkic". */
function StatusBadge({ published }: { published: boolean }) {
  return (
    <Badge variant={published ? "secondary" : "outline"}>
      {published ? "Opublikowany" : "Szkic"}
    </Badge>
  );
}

function EditLink({ product }: { product: ManagedProductRow }) {
  return (
    <Button
      variant="outline"
      size="sm"
      render={<Link href={`/manage/products/${product.id}`} />}
      nativeButton={false}
      aria-label={`Edytuj produkt: ${product.name}`}
    >
      Edytuj
    </Button>
  );
}

const priceText = (product: ManagedProductRow) =>
  product.price_from ? `od ${formatPrice(product.price_from)}` : "Brak ceny";

export function ManagedProductsTable({
  products,
}: {
  products: ManagedProductRow[];
}) {
  return (
    <>
      <div className="hidden md:block">
        <Table>
          <TableCaption className="sr-only">
            Produkty w Twoim zakresie
          </TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Nazwa</TableHead>
              <TableHead>Kategoria</TableHead>
              <TableHead>Cena</TableHead>
              <TableHead>Dostępność</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Akcje</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {products.map((product) => (
              <TableRow key={product.id}>
                <TableCell className="font-medium">{product.name}</TableCell>
                <TableCell>{product.category.name}</TableCell>
                <TableCell>{priceText(product)}</TableCell>
                <TableCell>
                  <AvailabilityBadge availability={product.availability} />
                </TableCell>
                <TableCell>
                  <StatusBadge published={product.is_published} />
                </TableCell>
                <TableCell>
                  <EditLink product={product} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <ul className="flex flex-col gap-3 md:hidden">
        {products.map((product) => (
          <li
            key={product.id}
            className="flex flex-col gap-3 rounded-2xl border bg-card p-4"
          >
            <div>
              <p className="font-medium">{product.name}</p>
              <p className="text-sm text-muted-foreground">
                {product.category.name} · {priceText(product)}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge published={product.is_published} />
              <AvailabilityBadge availability={product.availability} />
            </div>
            <EditLink product={product} />
          </li>
        ))}
      </ul>
    </>
  );
}
