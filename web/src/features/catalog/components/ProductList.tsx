"use client";

import { CloudAlertIcon, PackageSearchIcon } from "@hugeicons/core-free-icons";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { useCategories, useProducts } from "../hooks";
import { PAGE_SIZE, type ProductsQuery } from "../types";
import { positiveInt, productsHref } from "../urls";
import { CategoryFilter } from "./CategoryFilter";
import { ProductCard } from "./ProductCard";

const SEARCH_DELAY_MS = 300;

/** The address is the single source of truth: ?category=&search=&page= */
function useListQuery(): ProductsQuery {
  const params = useSearchParams();
  return {
    category: positiveInt(params.get("category")),
    search: params.get("search") ?? "",
    page: positiveInt(params.get("page")) ?? 1,
  };
}

export function ProductList() {
  const router = useRouter();
  const searchId = useId();
  const query = useListQuery();
  const [searchInput, setSearchInput] = useState(query.search);
  // The address is also changed from outside (the "show all" button, the back button). Then the
  // field must show it, or the debounce below would push the old text back into the address.
  // The value this component wrote itself is remembered, so that echo of our own change never
  // overwrites what the user is still typing.
  const [pushedSearch, setPushedSearch] = useState(query.search);
  const [seenSearch, setSeenSearch] = useState(query.search);
  if (query.search !== seenSearch) {
    setSeenSearch(query.search);
    if (query.search.trim() !== pushedSearch.trim()) {
      setSearchInput(query.search);
      setPushedSearch(query.search);
    }
  }
  const products = useProducts(query);
  const categories = useCategories();

  // Search as you type, but change the address (and ask the API) only after a short pause
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput.trim() !== query.search.trim()) {
        setPushedSearch(searchInput);
        router.replace(
          productsHref({ category: query.category, search: searchInput }),
        );
      }
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [searchInput, query.search, query.category, router]);

  const { data, isPending, isError, error, isPlaceholderData, refetch } =
    products;
  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <h1 className="text-3xl font-semibold">Produkty</h1>

      <div className="grid gap-6 md:grid-cols-[14rem_1fr]">
        <aside aria-label="Filtry">
          {categories.data ? (
            <CategoryFilter
              tree={categories.data}
              selected={query.category}
              search={query.search}
            />
          ) : categories.isError ? (
            <p className="text-sm text-muted-foreground">
              Nie udało się wczytać kategorii.{" "}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => categories.refetch()}
              >
                Spróbuj ponownie
              </button>
            </p>
          ) : null}
        </aside>

        <div className="flex min-w-0 flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor={searchId}>Szukaj po nazwie</Label>
            <Input
              id={searchId}
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              autoComplete="off"
            />
          </div>

          {isPending ? (
            <PageSpinner />
          ) : isError ? (
            <ListError
              error={error}
              onRetry={() => refetch()}
              keepSearch={query.search}
            />
          ) : (
            <div
              aria-busy={isPlaceholderData}
              className={cn(
                "flex flex-col gap-4 transition-opacity",
                isPlaceholderData && "opacity-60",
              )}
            >
              <p role="status" className="text-sm text-muted-foreground">
                Liczba produktów: {data.count}
              </p>

              {data.results.length === 0 ? (
                <PageMessage
                  heading="h2"
                  icon={PackageSearchIcon}
                  title="Brak produktów"
                  description="Nie znaleźliśmy produktów pasujących do wybranych filtrów."
                  action={
                    <Button
                      variant="outline"
                      render={<Link href={productsHref()} />}
                      nativeButton={false}
                    >
                      Pokaż wszystkie produkty
                    </Button>
                  }
                />
              ) : (
                <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {data.results.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </ul>
              )}

              {totalPages > 1 && (
                <nav
                  aria-label="Strony wyników"
                  className="flex items-center justify-between gap-4"
                >
                  <PageLink
                    label="Poprzednia"
                    query={{ ...query, page: query.page - 1 }}
                    disabled={data.previous === null}
                  />
                  <span className="text-sm text-muted-foreground">
                    Strona {query.page} z {totalPages}
                  </span>
                  <PageLink
                    label="Następna"
                    query={{ ...query, page: query.page + 1 }}
                    disabled={data.next === null}
                  />
                </nav>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PageLink({
  label,
  query,
  disabled,
}: {
  label: string;
  query: ProductsQuery;
  disabled: boolean;
}) {
  if (disabled) {
    return (
      <Button variant="outline" disabled>
        {label}
      </Button>
    );
  }
  return (
    <Button
      variant="outline"
      render={<Link href={productsHref(query)} />}
      nativeButton={false}
    >
      {label}
    </Button>
  );
}

/** A category or a page that does not exist (an old link) is not a connection problem. */
function ListError({
  error,
  onRetry,
  keepSearch,
}: {
  error: unknown;
  onRetry: () => void;
  keepSearch: string;
}) {
  const notFound =
    error instanceof ApiError &&
    (error.code === "CATEGORY_NOT_FOUND" || error.code === "NOT_FOUND");
  if (notFound) {
    return (
      <PageMessage
        heading="h2"
        icon={PackageSearchIcon}
        title="Nie znaleziono tej listy"
        description="Kategoria albo strona wyników nie istnieje."
        action={
          <Button
            render={<Link href={productsHref({ search: keepSearch })} />}
            nativeButton={false}
          >
            Wróć do listy produktów
          </Button>
        }
      />
    );
  }
  return (
    <PageMessage
      heading="h2"
      icon={CloudAlertIcon}
      title="Nie udało się wczytać produktów"
      description={errorMessage(error)}
      action={<Button onClick={onRetry}>Spróbuj ponownie</Button>}
    />
  );
}
