import { formatPrice } from "../availability";
import type { Variant } from "../types";
import { AvailabilityBadge } from "./AvailabilityBadge";

/** ["a"] -> "a", ["a", "b", "c"] -> "a, b i c" */
function joinLabels(labels: string[]): string {
  return labels.length < 2
    ? labels.join("")
    : `${labels.slice(0, -1).join(", ")} i ${labels[labels.length - 1]}`;
}

type VariantSummaryProps = {
  /** The chosen variant; undefined until every group has a choice. */
  variant: Variant | undefined;
  /** Labels of the groups still to choose, e.g. ["rozmiar", "kolor"]. */
  missing: string[];
  hasVariants: boolean;
};

/** Price, availability and stock appear only once the choice points at one variant. */
export function VariantSummary({
  variant,
  missing,
  hasVariants,
}: VariantSummaryProps) {
  return (
    // Announced by screen readers when the content changes
    <div aria-live="polite" className="flex flex-col gap-2">
      {!hasVariants ? (
        <p className="text-muted-foreground">
          Ten produkt nie ma jeszcze dostępnych wariantów.
        </p>
      ) : variant ? (
        <>
          <p className="text-3xl font-semibold">{formatPrice(variant.price)}</p>
          <div className="flex flex-wrap items-center gap-3">
            <AvailabilityBadge availability={variant.availability} />
            {variant.availability === "AVAILABLE" && (
              <span className="text-sm text-muted-foreground">
                Na stanie: {variant.stock} szt.
              </span>
            )}
          </div>
        </>
      ) : (
        <p className="text-muted-foreground">
          Wybierz {joinLabels(missing)}, aby zobaczyć cenę i dostępność.
        </p>
      )}
    </div>
  );
}
