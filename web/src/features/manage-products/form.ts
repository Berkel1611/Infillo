import type { JSONContent } from "@tiptap/react";
import type { Path } from "react-hook-form";

import type {
  ProductDetail,
  ProductInput,
  VariantInput,
} from "@/features/catalog/types";

/**
 * Values the form holds. Numbers and the category are strings here (that is what inputs give);
 * toInput() converts them. The id of an existing variant is called `variantId`, because
 * useFieldArray uses the key "id" for its own bookkeeping.
 */
export type VariantFields = {
  variantId?: number;
  color: string;
  material: string;
  size: string;
  price: string;
  stock: string;
  made_to_order: boolean;
};

export type ProductFormValues = {
  name: string;
  category_id: string;
  description: JSONContent | null;
  is_published: boolean;
  variants: VariantFields[];
};

export const emptyVariant = (): VariantFields => ({
  color: "",
  material: "",
  size: "",
  price: "",
  stock: "0",
  made_to_order: false,
});

export function toFormValues(product?: ProductDetail): ProductFormValues {
  if (!product) {
    return {
      name: "",
      category_id: "",
      description: null,
      is_published: false,
      variants: [emptyVariant()],
    };
  }
  return {
    name: product.name,
    category_id: String(product.category.id),
    description: product.description,
    is_published: product.is_published,
    variants: product.variants.map((variant) => ({
      variantId: variant.id,
      color: variant.color,
      material: variant.material,
      size: variant.size,
      price: variant.price,
      stock: String(variant.stock),
      made_to_order: variant.made_to_order,
    })),
  };
}

/** Form values -> the body of POST / PATCH /products. */
export function toInput(values: ProductFormValues): ProductInput {
  return {
    name: values.name.trim(),
    category_id: Number(values.category_id),
    ...(values.description && { description: values.description }),
    is_published: values.is_published,
    variants: values.variants.map((row): VariantInput => ({
      ...(row.variantId !== undefined && { id: row.variantId }),
      color: row.color.trim(),
      material: row.material.trim(),
      size: row.size.trim(),
      // A Polish keyboard types a comma; the API wants a dot
      price: row.price.trim().replace(",", "."),
      stock: Number(row.stock),
      made_to_order: row.made_to_order,
    })),
  };
}

/** The first pair of rows with the same color, material and size, or null. */
export function findDuplicateVariant(
  rows: VariantFields[],
): [number, number] | null {
  const seen = new Map<string, number>();
  for (const [index, row] of rows.entries()) {
    const key = [row.color, row.material, row.size]
      .map((part) => part.trim().toLowerCase())
      .join("\u0000");
    const first = seen.get(key);
    if (first !== undefined) {
      return [first, index];
    }
    seen.set(key, index);
  }
  return null;
}

/** Names of every field the server may report an error for (see applyServerErrors). */
export function serverFieldNames(
  variantCount: number,
): readonly Path<ProductFormValues>[] {
  const rowFields = ["color", "material", "size", "price", "stock"] as const;
  return [
    "name",
    "category_id",
    "description",
    "is_published",
    "variants",
    ...Array.from({ length: variantCount }, (_, index) =>
      rowFields.map(
        (field) => `variants.${index}.${field}` as Path<ProductFormValues>,
      ),
    ).flat(),
  ];
}

// --- validation rules (react-hook-form) ---

export const nameRules = {
  validate: (value: string) =>
    value.trim().length > 0 || "Podaj nazwę produktu.",
  maxLength: { value: 200, message: "Nazwa może mieć najwyżej 200 znaków." },
};

export const categoryRules = { required: "Wybierz kategorię." };

export const priceRules = {
  validate: (value: string) => {
    const price = value.trim().replace(",", ".");
    return (
      (/^\d{1,6}(\.\d{1,2})?$/.test(price) && Number(price) > 0) ||
      "Podaj cenę większą od zera, najwyżej z dwoma miejscami po przecinku."
    );
  },
};

export const stockRules = {
  validate: (value: string) =>
    /^\d+$/.test(value.trim()) || "Podaj liczbę całkowitą, 0 lub więcej.",
};

export const variantTextRules = {
  maxLength: { value: 50, message: "Wartość może mieć najwyżej 50 znaków." },
};
