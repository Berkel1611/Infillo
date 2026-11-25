import type { ProductsQuery } from "./types";

/** Address of the public list for a query; defaults (all categories, page 1) are left out. */
export function productsHref({
  category,
  search,
  page,
}: Partial<ProductsQuery> = {}): string {
  const params = new URLSearchParams();
  if (category != null) {
    params.set("category", String(category));
  }
  if (search?.trim()) {
    params.set("search", search.trim());
  }
  if (page && page > 1) {
    params.set("page", String(page));
  }
  const query = params.toString();
  return query ? `/products?${query}` : "/products";
}

/** Reads a positive integer from the address; anything else is "not given". */
export function positiveInt(value: string | null): number | null {
  if (value === null || !/^\d+$/.test(value)) {
    return null;
  }
  const number = Number(value);
  return number > 0 ? number : null;
}
