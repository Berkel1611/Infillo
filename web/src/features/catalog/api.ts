import type { User } from "@/features/auth/types";
import { api } from "@/shared/api/client";

import type {
  Category,
  CategoryInput,
  CategoryNode,
  ManagedProductRow,
  Moderator,
  Page,
  ProductDetail,
  ProductInput,
  ProductRow,
  ProductsQuery,
} from "./types";

function listParams({ category, search, page }: ProductsQuery): string {
  const params = new URLSearchParams({ page: String(page) });
  if (category !== null) {
    params.set("category", String(category));
  }
  if (search.trim()) {
    params.set("search", search.trim());
  }
  return params.toString();
}

export const categoriesApi = {
  tree: () => api.get<CategoryNode[]>("/categories"),
  managed: () => api.get<Category[]>("/categories/managed"),
  create: (input: CategoryInput) => api.post<Category>("/categories", input),
  update: (id: number, input: CategoryInput) =>
    api.patch<Category>(`/categories/${id}`, input),
  remove: (id: number) => api.delete(`/categories/${id}`),
  moderators: (id: number) =>
    api.get<Moderator[]>(`/categories/${id}/moderators`),
  /** Accounts that may be assigned to a category (administrators only; max 100). */
  moderatorAccounts: () =>
    api.get<Page<User>>("/users?role=moderator&page_size=100"),
  setModerators: (id: number, moderatorIds: number[]) =>
    api.put<Moderator[]>(`/categories/${id}/moderators`, {
      moderator_ids: moderatorIds,
    }),
};

export const productsApi = {
  list: (query: ProductsQuery) =>
    api.get<Page<ProductRow>>(`/products?${listParams(query)}`),
  managed: (query: ProductsQuery) =>
    api.get<Page<ManagedProductRow>>(`/products/managed?${listParams(query)}`),
  get: (id: number) => api.get<ProductDetail>(`/products/${id}`),
  create: (input: ProductInput) => api.post<ProductDetail>("/products", input),
  update: (id: number, input: Partial<ProductInput>) =>
    api.patch<ProductDetail>(`/products/${id}`, input),
};
