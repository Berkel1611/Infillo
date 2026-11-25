"use client";

import { CloudAlertIcon, PackageSearchIcon } from "@hugeicons/core-free-icons";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { isEmptyDocument } from "@/shared/rich-text/is-empty";
import { RichTextView } from "@/shared/rich-text/RichTextView";
import { Button } from "@/shared/ui/button";

import { useProduct } from "../hooks";
import type { ProductDetail as Product } from "../types";
import { positiveInt } from "../urls";
import {
  type AttributeKey,
  effectiveSelection,
  missingGroupLabels,
  optionGroups,
  resolveVariant,
  type Selection,
} from "../variant-options";
import { CategoryPath } from "./CategoryPath";
import { VariantSelector } from "./VariantSelector";
import { VariantSummary } from "./VariantSummary";

const backToList = (
  <Button render={<Link href="/products" />} nativeButton={false}>
    Wróć do listy produktów
  </Button>
);

export function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const productId = positiveInt(id);
  const { data, isPending, isError, error, refetch } = useProduct(productId);

  if (productId === null || (isError && isNotFound(error))) {
    return (
      <PageMessage
        icon={PackageSearchIcon}
        title="Nie znaleziono produktu"
        description="Ten produkt nie istnieje albo nie jest już dostępny."
        action={backToList}
      />
    );
  }
  if (isPending) {
    return <PageSpinner />;
  }
  if (isError) {
    return (
      <PageMessage
        icon={CloudAlertIcon}
        title="Nie udało się wczytać produktu"
        description={errorMessage(error)}
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  // key: another product starts with a clean selection
  return <ProductView key={data.id} product={data} />;
}

function ProductView({ product }: { product: Product }) {
  // Only what the customer clicked is stored; the rest (which variant, what is missing)
  // is derived on every render, so it can never go out of sync
  const [chosen, setChosen] = useState<Selection>({});
  const groups = optionGroups(product.variants);
  const selection = effectiveSelection(groups, chosen);
  const variant = resolveVariant(product.variants, groups, selection);

  function choose(key: AttributeKey, value: string) {
    setChosen({ ...chosen, [key]: value });
  }

  return (
    // md:min-h: from the md breakpoint the article fills the space between the header (4rem)
    // and the footer (about 4.25rem), so the side panel can reach the bottom even when the
    // description is short. The value is a little smaller than the exact sum on purpose.
    <article className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8 md:min-h-[calc(100svh-8.5rem)]">
      <CategoryPath path={product.category_path} />

      <header className="flex flex-col gap-3">
        <h1 className="text-3xl font-semibold">{product.name}</h1>
        {!product.is_published && (
          // Drafts are visible only to those who manage the category
          <span className="w-fit rounded-4xl border px-2 py-0.5 text-xs font-medium">
            Szkic: widoczny tylko dla zarządzających
          </span>
        )}
      </header>

      <div className="grid flex-1 gap-8 md:grid-cols-[1fr_20rem]">
        {/* The panel comes first on a phone, so the choice is not buried under the text */}
        <aside
          aria-label="Wybór wariantu"
          className="flex flex-col gap-5 rounded-2xl border bg-card p-5 md:order-last"
        >
          <VariantSelector
            variants={product.variants}
            groups={groups}
            selection={selection}
            hasUserChoice={Object.keys(chosen).length > 0}
            onChange={choose}
            onClear={() => setChosen({})}
          />
          <VariantSummary
            variant={variant}
            missing={missingGroupLabels(groups, selection)}
            hasVariants={product.variants.length > 0}
          />
        </aside>

        <section
          aria-labelledby="description-heading"
          className="flex flex-col gap-2"
        >
          <h2 id="description-heading" className="text-xl font-semibold">
            Opis
          </h2>
          {isEmptyDocument(product.description) ? (
            <p className="text-muted-foreground">
              Ten produkt nie ma jeszcze opisu.
            </p>
          ) : (
            <RichTextView content={product.description} />
          )}
        </section>
      </div>
    </article>
  );
}

function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND";
}
