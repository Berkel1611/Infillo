"use client";

import { Add01Icon, Delete02Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useRef } from "react";
import {
  Controller,
  type Control,
  type FieldErrors,
  type UseFieldArrayRemove,
  type UseFormRegister,
} from "react-hook-form";

import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import {
  priceRules,
  type ProductFormValues,
  stockRules,
  variantTextRules,
} from "../form";

type VariantsEditorProps = {
  rowIds: string[];
  control: Control<ProductFormValues>;
  register: UseFormRegister<ProductFormValues>;
  errors: FieldErrors<ProductFormValues>;
  /** Error of the whole list (e.g. two identical variants). */
  listError?: string;
  onAdd: () => void;
  onRemove: UseFieldArrayRemove;
};

/** One fieldset per variant; a list error (duplicates) is shown under the last row. */
export function VariantsEditor({
  rowIds,
  control,
  register,
  errors,
  listError,
  onAdd,
  onRemove,
}: VariantsEditorProps) {
  const addButton = useRef<HTMLButtonElement>(null);

  return (
    <div className="flex flex-col gap-4">
      {rowIds.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Produkt nie ma jeszcze wariantów. Bez nich nie można go opublikować.
        </p>
      )}

      {rowIds.map((rowId, index) => {
        const rowErrors = errors.variants?.[index];
        return (
          <fieldset
            key={rowId}
            className="flex flex-col gap-4 rounded-2xl border p-4"
          >
            <legend className="px-1 text-sm font-medium">
              Wariant {index + 1}
            </legend>

            <div className="grid gap-5 sm:grid-cols-3">
              <FormField label="Rozmiar" error={rowErrors?.size?.message}>
                {(field) => (
                  <Input
                    {...field}
                    {...register(`variants.${index}.size`, variantTextRules)}
                  />
                )}
              </FormField>
              <FormField label="Kolor" error={rowErrors?.color?.message}>
                {(field) => (
                  <Input
                    {...field}
                    {...register(`variants.${index}.color`, variantTextRules)}
                  />
                )}
              </FormField>
              <FormField label="Materiał" error={rowErrors?.material?.message}>
                {(field) => (
                  <Input
                    {...field}
                    {...register(
                      `variants.${index}.material`,
                      variantTextRules,
                    )}
                  />
                )}
              </FormField>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <FormField label="Cena (zł)" error={rowErrors?.price?.message}>
                {(field) => (
                  <Input
                    {...field}
                    inputMode="decimal"
                    autoComplete="off"
                    {...register(`variants.${index}.price`, priceRules)}
                  />
                )}
              </FormField>
              <FormField
                label="Stan magazynowy"
                error={rowErrors?.stock?.message}
              >
                {(field) => (
                  <Input
                    {...field}
                    inputMode="numeric"
                    autoComplete="off"
                    {...register(`variants.${index}.stock`, stockRules)}
                  />
                )}
              </FormField>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <Controller
                control={control}
                name={`variants.${index}.made_to_order`}
                render={({ field }) => (
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id={`${rowId}-made-to-order`}
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                    <Label htmlFor={`${rowId}-made-to-order`}>
                      Na zamówienie (gdy brak na stanie)
                    </Label>
                  </div>
                )}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                aria-label={`Usuń wariant ${index + 1}`}
                onClick={() => {
                  onRemove(index);
                  // The focused button disappears with the row: send focus somewhere sensible
                  addButton.current?.focus();
                }}
              >
                <HugeiconsIcon icon={Delete02Icon} aria-hidden />
                Usuń
              </Button>
            </div>
          </fieldset>
        );
      })}

      {listError && (
        <p role="alert" className="text-sm text-destructive">
          {listError}
        </p>
      )}

      <Button
        ref={addButton}
        type="button"
        variant="outline"
        className="w-fit"
        onClick={onAdd}
      >
        <HugeiconsIcon icon={Add01Icon} aria-hidden />
        Dodaj wariant
      </Button>
    </div>
  );
}
