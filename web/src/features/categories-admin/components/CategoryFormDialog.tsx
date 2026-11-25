"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import {
  MAX_CATEGORY_DEPTH,
  type TreeEntry,
} from "@/features/catalog/category-labels";
import { useSaveCategory } from "@/features/catalog/hooks";
import { applyServerErrors } from "@/shared/api/apply-server-errors";
import { errorMessage } from "@/shared/api/error-messages";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { FormAlert } from "@/shared/ui/form-alert";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";

/** Create a category under `parentId` (null = a root), or edit the one with `id`. */
export type CategoryFormTarget =
  { mode: "create"; parentId: number | null } | { mode: "edit"; id: number };

type FormValues = { name: string; parent_id: string }; // "" = a root category

const selectClass =
  "h-9 w-full rounded-4xl border border-input bg-input/30 px-3 text-base outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive md:text-sm";

const nameRules = {
  validate: (value: string) =>
    value.trim().length > 0 || "Podaj nazwę kategorii.",
  maxLength: { value: 100, message: "Nazwa może mieć najwyżej 100 znaków." },
};

type CategoryFormDialogProps = {
  /** Where the focus goes when the dialog closes (see CategoriesAdminPage). */
  finalFocus?: () => HTMLElement | null;
  /** null = closed. */
  target: CategoryFormTarget | null;
  entries: TreeEntry[];
  onClose: () => void;
};

export function CategoryFormDialog({
  target,
  entries,
  finalFocus,
  onClose,
}: CategoryFormDialogProps) {
  return (
    <Dialog
      open={target !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent finalFocus={finalFocus}>
        {target && (
          // key: every opening starts with a clean form
          <CategoryForm
            key={target.mode === "edit" ? target.id : `new-${target.parentId}`}
            target={target}
            entries={entries}
            onClose={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

function CategoryForm({
  target,
  entries,
  onClose,
}: {
  target: CategoryFormTarget;
  entries: TreeEntry[];
  onClose: () => void;
}) {
  const saveCategory = useSaveCategory();
  const [generalError, setGeneralError] = useState<unknown>(null);
  const edited =
    target.mode === "edit"
      ? entries.find((entry) => entry.id === target.id)
      : undefined;

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: {
      name: edited?.name ?? "",
      parent_id: String(
        (target.mode === "edit" ? edited?.parentId : target.parentId) ?? "",
      ),
    },
  });

  // Where the category may go: never into itself or its own subtree, and not so deep that
  // it (with everything below it) would pass the third level. The server checks it again.
  const parentChoices = entries.filter(
    (entry) =>
      !edited?.subtreeIds.includes(entry.id) &&
      entry.depth + 1 + (edited?.height ?? 0) <= MAX_CATEGORY_DEPTH,
  );

  const onSubmit = handleSubmit((values) => {
    setGeneralError(null);
    const input = {
      name: values.name.trim(),
      parent_id: values.parent_id === "" ? null : Number(values.parent_id),
    };
    saveCategory.mutate(
      { id: edited?.id, input },
      {
        onSuccess: () => {
          toast.success(
            target.mode === "edit"
              ? "Zapisano kategorię."
              : "Dodano kategorię.",
          );
          onClose();
        },
        onError: (error) => {
          if (!applyServerErrors(error, setError, ["name", "parent_id"])) {
            setGeneralError(error);
          }
        },
      },
    );
  });

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-5">
      <DialogHeader>
        <DialogTitle>
          {target.mode === "edit" ? "Edycja kategorii" : "Nowa kategoria"}
        </DialogTitle>
        <DialogDescription>
          Kategorie mogą mieć najwyżej {MAX_CATEGORY_DEPTH} poziomy.
        </DialogDescription>
      </DialogHeader>

      {generalError !== null && (
        <FormAlert title="Nie udało się zapisać kategorii">
          {errorMessage(generalError)}
        </FormAlert>
      )}

      <FormField label="Nazwa" error={errors.name?.message}>
        {(field) => (
          <Input
            {...field}
            autoComplete="off"
            {...register("name", nameRules)}
          />
        )}
      </FormField>

      <FormField label="Kategoria nadrzędna" error={errors.parent_id?.message}>
        {(field) => (
          <select {...field} className={selectClass} {...register("parent_id")}>
            <option value="">Brak (kategoria główna)</option>
            {parentChoices.map((entry) => (
              <option key={entry.id} value={entry.id}>
                {entry.label}
              </option>
            ))}
          </select>
        )}
      </FormField>

      <DialogFooter>
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button type="submit" disabled={saveCategory.isPending}>
          {saveCategory.isPending && <Spinner data-icon="inline-start" />}
          Zapisz
        </Button>
      </DialogFooter>
    </form>
  );
}
