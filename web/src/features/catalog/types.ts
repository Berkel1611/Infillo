import type { JSONContent } from "@tiptap/react";

export const PAGE_SIZE = 20; // the API default (StandardPagination)

export type Availability = "AVAILABLE" | "MADE_TO_ORDER" | "OUT_OF_STOCK";

/** Page of a list: the DRF pagination format. */
export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

// --- categories ---

export type CategoryRef = { id: number; name: string };

/** GET /categories: the whole tree. */
export type CategoryNode = {
  id: number;
  name: string;
  children: CategoryNode[];
};

/** One category without children (POST / PATCH answers, GET /categories/managed). */
export type Category = { id: number; name: string; parent_id: number | null };

/** Body of POST / PATCH /categories; a missing key means "unchanged". */
export type CategoryInput = { name?: string; parent_id?: number | null };

export type Moderator = { id: number; username: string };

// --- products ---

/** Prices travel as text ("49.00"), never as a JSON number. */
export type Variant = {
  id: number;
  color: string;
  material: string;
  size: string;
  price: string;
  stock: number;
  made_to_order: boolean;
  availability: Availability;
};

export type ProductRow = {
  id: number;
  name: string;
  category: CategoryRef;
  price_from: string | null;
  availability: Availability;
};

export type ManagedProductRow = ProductRow & { is_published: boolean };

export type ProductDetail = {
  id: number;
  name: string;
  description: JSONContent;
  is_published: boolean;
  category: CategoryRef;
  /** From the root down to the product's category. */
  category_path: CategoryRef[];
  price_from: string | null;
  availability: Availability;
  variants: Variant[];
};

/** Query of the public list; `category` null means all categories. */
export type ProductsQuery = {
  category: number | null;
  search: string;
  page: number;
};

export type VariantInput = {
  id?: number;
  color?: string;
  material?: string;
  size?: string;
  price: string;
  stock: number;
  made_to_order: boolean;
};

/** Body of POST /products; PATCH accepts any subset (`variants` present = replace the list). */
export type ProductInput = {
  name: string;
  description?: JSONContent;
  category_id: number;
  is_published?: boolean;
  variants?: VariantInput[];
};
