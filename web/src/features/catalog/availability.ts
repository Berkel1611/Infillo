import type { Availability } from "./types";

/** Availability is always shown as text, never by color alone (W-OG-2). */
export const availabilityLabels: Record<Availability, string> = {
  AVAILABLE: "Dostępny",
  MADE_TO_ORDER: "Na zamówienie",
  OUT_OF_STOCK: "Niedostępny",
};

const priceFormat = new Intl.NumberFormat("pl-PL", {
  style: "currency",
  currency: "PLN",
});

/** "49.00" (the API sends prices as text) -> "49,00 zł". */
export function formatPrice(price: string): string {
  return priceFormat.format(Number(price));
}

/** "Kolor · materiał · rozmiar", skipping empty parts; a variant with none is the basic one. */
export function variantLabel(variant: {
  color: string;
  material: string;
  size: string;
}): string {
  const parts = [variant.color, variant.material, variant.size].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "Wariant podstawowy";
}
