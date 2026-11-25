"use client";

import { CloudAlertIcon, PackageSearchIcon } from "@hugeicons/core-free-icons";
import Link from "next/link";
import { useEffect, useId, useState } from "react";

import { categoryOptions } from "@/features/catalog/category-labels";
import {
  useManagedCategories,
  useManagedProducts,
} from "@/features/catalog/hooks";
import { PAGE_SIZE, type ProductsQuery } from "@/features/catalog/types";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { ManagedProductsTable } from "./ManagedProductsTable";

const SEARCH_DELAY_MS = 300;
const INITIAL_QUERY: ProductsQuery = { category: null, search: "", page: 1 };

const selectClass =
  "h-9 w-full rounded-4xl border border-input bg-input/30 px-3 text-base outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 md:text-sm";

export function ManagedProductsPage() {
  const categoryId = useId();
  const searchId = useId();
  const [query, setQuery] = useState<ProductsQuery>(INITIAL_QUERY);
  const [searchInput, setSearchInput] = useState("");
  const products = useManagedProducts(query);
  const categories = useManagedCategories();

  // Search as you type, but ask the API only after a short pause
  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery((q) =>
        q.search === searchInput.trim()
          ? q
          : { ...q, search: searchInput.trim(), page: 1 },
      );
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const { data, isPending, isError, error, isPlaceholderData, refetch } =
    products;
  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;
  const options = categoryOptions(categories.data ?? []);

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold">Moje produkty</h1>
        <Button
          render={<Link href="/manage/products/new" />}
          nativeButton={false}
        >
          Dodaj produkt
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <div className="flex flex-col gap-2 sm:w-72">
          <Label htmlFor={categoryId}>Kategoria</Label>
          <select
            id={categoryId}
            value={query.category ?? ""}
            onChange={(event) =>
              setQuery((q) => ({
                ...q,
                category: event.target.value
                  ? Number(event.target.value)
                  : null,
                page: 1,
              }))
            }
            className={selectClass}
          >
            <option value="">Wszystkie moje kategorie</option>
            {options.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor={searchId}>Szukaj po nazwie</Label>
          <Input
            id={searchId}
            type="search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            autoComplete="off"
          />
        </div>
      </div>

      {isPending ? (
        <PageSpinner />
      ) : isError ? (
        <PageMessage
          heading="h2"
          icon={CloudAlertIcon}
          title="Nie udało się wczytać produktów"
          description={errorMessage(error)}
          action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
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
              description="Nie ma produktów pasujących do filtrów. Możesz dodać pierwszy."
            />
          ) : (
            <ManagedProductsTable products={data.results} />
          )}

          {totalPages > 1 && (
            <nav
              aria-label="Strony wyników"
              className="flex items-center justify-between gap-4"
            >
              <Button
                variant="outline"
                disabled={data.previous === null}
                onClick={() => setQuery((q) => ({ ...q, page: q.page - 1 }))}
              >
                Poprzednia
              </Button>
              <span className="text-sm text-muted-foreground">
                Strona {query.page} z {totalPages}
              </span>
              <Button
                variant="outline"
                disabled={data.next === null}
                onClick={() => setQuery((q) => ({ ...q, page: q.page + 1 }))}
              >
                Następna
              </Button>
            </nav>
          )}
        </div>
      )}
    </div>
  );
}
