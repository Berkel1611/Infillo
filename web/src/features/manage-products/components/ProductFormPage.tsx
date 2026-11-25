"use client";

import {
  CloudAlertIcon,
  LockIcon,
  PackageSearchIcon,
} from "@hugeicons/core-free-icons";
import Link from "next/link";
import { useParams } from "next/navigation";

import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";
import { useManagedCategories, useProduct } from "@/features/catalog/hooks";
import { positiveInt } from "@/features/catalog/urls";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { ProductForm } from "./ProductForm";

const backToList = (
  <Button render={<Link href="/manage/products" />} nativeButton={false}>
    Wróć do listy produktów
  </Button>
);

/** A new product (no id in the address) or the edit of an existing one. */
export function ProductFormPage({ mode }: { mode: "new" | "edit" }) {
  const { id } = useParams<{ id?: string }>();
  const productId = mode === "edit" ? positiveInt(id ?? null) : null;
  const product = useProduct(productId);
  const categories = useManagedCategories();

  if (mode === "edit" && productId === null) {
    return <NotFound />;
  }
  if (product.isError) {
    return product.error instanceof ApiError &&
      product.error.code === "PRODUCT_NOT_FOUND" ? (
      <NotFound />
    ) : (
      <PageMessage
        icon={CloudAlertIcon}
        title="Nie udało się wczytać produktu"
        description={errorMessage(product.error)}
        action={
          <Button onClick={() => product.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }
  if (categories.isError) {
    return (
      <PageMessage
        icon={CloudAlertIcon}
        title="Nie udało się wczytać kategorii"
        description={errorMessage(categories.error)}
        action={
          <Button onClick={() => categories.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }
  if (categories.isPending || (mode === "edit" && product.isPending)) {
    return <PageSpinner />;
  }

  // A published product is public, so it can be opened here even from a category the user
  // does not manage; saving would be refused (403), so say it before the user types anything
  if (
    mode === "edit" &&
    product.data &&
    !categories.data.some(
      (category) => category.id === product.data.category.id,
    )
  ) {
    return (
      <PageMessage
        icon={LockIcon}
        title="Brak dostępu do tego produktu"
        description="Nie zarządzasz kategorią, w której jest ten produkt."
        action={backToList}
      />
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8">
      <h1 className="text-3xl font-semibold">
        {product.data ? `Edycja: ${product.data.name}` : "Nowy produkt"}
      </h1>
      {/* key: opening another product starts the form from scratch */}
      <ProductForm
        key={product.data?.id ?? "new"}
        product={product.data}
        categories={categories.data}
      />
    </div>
  );
}

function NotFound() {
  return (
    <PageMessage
      icon={PackageSearchIcon}
      title="Nie znaleziono produktu"
      description="Ten produkt nie istnieje albo nie masz do niego dostępu."
      action={backToList}
    />
  );
}
