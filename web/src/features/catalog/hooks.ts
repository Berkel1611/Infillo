import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { categoriesApi, productsApi } from "./api";
import type { CategoryInput, ProductInput, ProductsQuery } from "./types";

// Keys are nested on purpose: invalidating ["products"] refreshes lists and details together
export const catalogKeys = {
  categories: ["categories"] as const,
  tree: ["categories", "tree"] as const,
  managedCategories: ["categories", "managed"] as const,
  moderators: (id: number) => ["categories", "moderators", id] as const,
  products: ["products"] as const,
  list: (query: ProductsQuery) => ["products", "list", query] as const,
  managedList: (query: ProductsQuery) =>
    ["products", "managed", query] as const,
  product: (id: number) => ["products", "detail", id] as const,
};

// --- queries ---

export function useCategories() {
  return useQuery({
    queryKey: catalogKeys.tree,
    queryFn: categoriesApi.tree,
  });
}

export function useManagedCategories() {
  return useQuery({
    queryKey: catalogKeys.managedCategories,
    queryFn: categoriesApi.managed,
  });
}

export function useCategoryModerators(id: number | null) {
  return useQuery({
    queryKey: catalogKeys.moderators(id ?? 0),
    queryFn: () => categoriesApi.moderators(id as number),
    enabled: id !== null,
  });
}

export function useProducts(query: ProductsQuery) {
  return useQuery({
    queryKey: catalogKeys.list(query),
    queryFn: () => productsApi.list(query),
    // The previous page stays on screen while the next one loads
    placeholderData: keepPreviousData,
  });
}

export function useManagedProducts(query: ProductsQuery) {
  return useQuery({
    queryKey: catalogKeys.managedList(query),
    queryFn: () => productsApi.managed(query),
    placeholderData: keepPreviousData,
  });
}

/** `id` null (a malformed address) means "do not ask the API". */
export function useProduct(id: number | null) {
  return useQuery({
    queryKey: catalogKeys.product(id ?? 0),
    queryFn: () => productsApi.get(id as number),
    enabled: id !== null,
  });
}

// --- mutations ---

export function useSaveProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      input,
    }: {
      id?: number;
      input: Partial<ProductInput>;
    }) =>
      id === undefined
        ? productsApi.create(input as ProductInput)
        : productsApi.update(id, input),
    // Returned promise: the mutation lasts until the lists are refreshed
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: catalogKeys.products }),
  });
}

export function useSaveCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: CategoryInput }) =>
      id === undefined
        ? categoriesApi.create(input)
        : categoriesApi.update(id, input),
    // Products show the category name, so their lists are stale too
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: catalogKeys.categories }),
        queryClient.invalidateQueries({ queryKey: catalogKeys.products }),
      ]),
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => categoriesApi.remove(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: catalogKeys.categories }),
  });
}

export function useSetModerators() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      moderatorIds,
    }: {
      id: number;
      moderatorIds: number[];
    }) => categoriesApi.setModerators(id, moderatorIds),
    onSuccess: (_moderators, { id }) =>
      queryClient.invalidateQueries({ queryKey: catalogKeys.moderators(id) }),
  });
}
