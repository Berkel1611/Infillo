"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  Controller,
  type FieldError,
  useFieldArray,
  useForm,
} from "react-hook-form";
import { toast } from "sonner";

import {
  categoryOptions,
  type CategoryOption,
} from "@/features/catalog/category-labels";
import { useSaveProduct } from "@/features/catalog/hooks";
import type { ProductDetail } from "@/features/catalog/types";
import { applyServerErrors } from "@/shared/api/apply-server-errors";
import { errorMessage } from "@/shared/api/error-messages";
import { RichTextEditor } from "@/shared/rich-text/RichTextEditor";
import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
import { FieldGroup } from "@/shared/ui/field";
import { FormAlert } from "@/shared/ui/form-alert";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Spinner } from "@/shared/ui/spinner";

import {
  categoryRules,
  emptyVariant,
  findDuplicateVariant,
  nameRules,
  type ProductFormValues,
  serverFieldNames,
  toFormValues,
  toInput,
} from "../form";
import { VariantsEditor } from "./VariantsEditor";

type ProductFormProps = {
  /** Undefined = a new product. */
  product?: ProductDetail;
  /** Categories the user may put products in (GET /categories/managed). */
  categories: { id: number; name: string; parent_id: number | null }[];
};

const selectClass =
  "h-9 w-full rounded-4xl border border-input bg-input/30 px-3 text-base outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive md:text-sm";

export function ProductForm({ product, categories }: ProductFormProps) {
  const router = useRouter();
  const saveProduct = useSaveProduct();
  const [generalError, setGeneralError] = useState<unknown>(null);
  const options: CategoryOption[] = categoryOptions(categories);

  const {
    register,
    control,
    handleSubmit,
    setError,
    clearErrors,
    getValues,
    formState: { errors },
  } = useForm<ProductFormValues>({ defaultValues: toFormValues(product) });
  const rows = useFieldArray({ control, name: "variants" });

  const submit = handleSubmit((values) => {
    setGeneralError(null);
    const duplicate = findDuplicateVariant(values.variants);
    if (duplicate) {
      setError("variants", {
        type: "duplicate",
        message: `Warianty ${duplicate[0] + 1} i ${duplicate[1] + 1} mają ten sam rozmiar, kolor i materiał.`,
      });
      return;
    }

    saveProduct.mutate(
      { id: product?.id, input: toInput(values) },
      {
        onSuccess: () => {
          toast.success(product ? "Zapisano produkt." : "Dodano produkt.");
          router.push("/manage/products");
        },
        onError: (error) => {
          const names = serverFieldNames(getValues("variants").length);
          if (!applyServerErrors(error, setError, names)) {
            setGeneralError(error);
          }
        },
      },
    );
  });

  // The error of the whole variants list is set by hand (a duplicate), so no field rule ever
  // clears it, and handleSubmit refuses to run while any error is set. Clear it first;
  // the duplicate check runs again inside the submit handler.
  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    clearErrors("variants");
    return submit(event);
  };

  const variantsError =
    errors.variants?.message ?? errors.variants?.root?.message;

  return (
    <form onSubmit={onSubmit} noValidate>
      <FieldGroup>
        {generalError !== null && (
          <FormAlert title="Nie udało się zapisać produktu">
            {errorMessage(generalError)}
          </FormAlert>
        )}

        <FormField label="Nazwa produktu" error={errors.name?.message}>
          {(field) => (
            <Input
              {...field}
              autoComplete="off"
              {...register("name", nameRules)}
            />
          )}
        </FormField>

        <FormField
          label="Kategoria"
          description="Dostępne są tylko kategorie, którymi zarządzasz."
          error={errors.category_id?.message}
        >
          {(field) => (
            <select
              {...field}
              className={selectClass}
              {...register("category_id", categoryRules)}
            >
              <option value="">Wybierz kategorię</option>
              {options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          )}
        </FormField>

        <Controller
          control={control}
          name="description"
          render={({ field }) => (
            <FormField
              label="Opis"
              description="Dozwolone: nagłówki, pogrubienie, kursywa, listy i linki http(s)."
              // description is an object (JSON), so react-hook-form types its error loosely
              error={(errors.description as FieldError | undefined)?.message}
            >
              {(control) => (
                <RichTextEditor
                  {...control}
                  label="Opis produktu"
                  initialContent={field.value}
                  onChange={field.onChange}
                />
              )}
            </FormField>
          )}
        />

        <fieldset className="flex flex-col gap-4">
          <legend className="mb-2 text-base font-medium">Warianty</legend>
          <VariantsEditor
            rowIds={rows.fields.map((row) => row.id)}
            control={control}
            register={register}
            errors={errors}
            listError={variantsError}
            onAdd={() => {
              clearErrors("variants");
              rows.append(emptyVariant());
            }}
            onRemove={(index) => {
              clearErrors("variants");
              rows.remove(index);
            }}
          />
        </fieldset>

        <Controller
          control={control}
          name="is_published"
          render={({ field }) => (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="is-published"
                  aria-describedby="is-published-hint"
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
                <Label htmlFor="is-published">Opublikuj produkt</Label>
              </div>
              <p
                id="is-published-hint"
                className="text-sm text-muted-foreground"
              >
                Opublikowany produkt widzą wszyscy. Wymaga opisu i co najmniej
                jednego wariantu. Szkic widzą tylko osoby, które zarządzają jego
                kategorią.
              </p>
            </div>
          )}
        />

        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={saveProduct.isPending}>
            {saveProduct.isPending && <Spinner data-icon="inline-start" />}
            {saveProduct.isPending ? "Zapisywanie..." : "Zapisz produkt"}
          </Button>
          <Button
            variant="outline"
            render={<Link href="/manage/products" />}
            nativeButton={false}
          >
            Anuluj
          </Button>
        </div>
      </FieldGroup>
    </form>
  );
}
