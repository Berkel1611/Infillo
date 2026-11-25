"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import {
  useCategoryModerators,
  useModeratorAccounts,
  useSetModerators,
} from "@/features/catalog/hooks";
import { errorMessage } from "@/shared/api/error-messages";
import { PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
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
import { Label } from "@/shared/ui/label";
import { Spinner } from "@/shared/ui/spinner";

type ModeratorAssignDialogProps = {
  /** Where the focus goes when the dialog closes (see CategoriesAdminPage). */
  finalFocus?: () => HTMLElement | null;
  /** null = closed. */
  category: { id: number; name: string } | null;
  onClose: () => void;
};

export function ModeratorAssignDialog({
  category,
  finalFocus,
  onClose,
}: ModeratorAssignDialogProps) {
  return (
    <Dialog
      open={category !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent finalFocus={finalFocus}>
        {category && (
          <AssignForm key={category.id} category={category} onClose={onClose} />
        )}
      </DialogContent>
    </Dialog>
  );
}

function AssignForm({
  category,
  onClose,
}: {
  category: { id: number; name: string };
  onClose: () => void;
}) {
  const accounts = useModeratorAccounts();
  const assigned = useCategoryModerators(category.id);
  const setModerators = useSetModerators();
  const [generalError, setGeneralError] = useState<unknown>(null);
  // null = nothing changed yet: show what is stored. Only the user's edits live in state.
  const [draft, setDraft] = useState<Set<number> | null>(null);

  const selected =
    draft ?? new Set((assigned.data ?? []).map((moderator) => moderator.id));

  function toggle(id: number, checked: boolean) {
    const next = new Set(selected);
    if (checked) {
      next.add(id);
    } else {
      next.delete(id);
    }
    setDraft(next);
  }

  function save() {
    setGeneralError(null);
    setModerators.mutate(
      { id: category.id, moderatorIds: [...selected] },
      {
        onSuccess: () => {
          toast.success("Zapisano przydział moderatorów.");
          onClose();
        },
        onError: setGeneralError,
      },
    );
  }

  const loading = accounts.isPending || assigned.isPending;
  const failed = accounts.isError || assigned.isError;

  return (
    <div className="grid gap-5">
      <DialogHeader>
        <DialogTitle>Moderatorzy: {category.name}</DialogTitle>
        <DialogDescription>
          Moderator zarządza produktami w tej kategorii i we wszystkich jej
          podkategoriach.
        </DialogDescription>
      </DialogHeader>

      {generalError !== null && (
        <FormAlert title="Nie udało się zapisać przydziału">
          {errorMessage(generalError)}
        </FormAlert>
      )}

      {loading ? (
        <PageSpinner />
      ) : failed ? (
        <FormAlert
          title="Nie udało się wczytać moderatorów"
          focusOnShow={false}
        >
          {errorMessage(accounts.error ?? assigned.error)}
        </FormAlert>
      ) : accounts.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nie ma jeszcze kont z rolą moderatora. Nadaj ją w{" "}
          <Link href="/admin/users" className="underline underline-offset-4">
            panelu użytkowników
          </Link>
          .
        </p>
      ) : (
        <fieldset className="flex max-h-72 flex-col gap-3 overflow-y-auto">
          <legend className="mb-2 text-sm font-medium">
            Wybierz moderatorów
          </legend>
          {accounts.data.map((account) => (
            <div key={account.id} className="flex items-center gap-2">
              <Checkbox
                id={`moderator-${account.id}`}
                checked={selected.has(account.id)}
                onCheckedChange={(checked) => toggle(account.id, checked)}
              />
              <Label htmlFor={`moderator-${account.id}`}>
                {account.username}
                <span className="font-normal text-muted-foreground">
                  {" "}
                  ({account.email})
                </span>
              </Label>
            </div>
          ))}
        </fieldset>
      )}

      <DialogFooter>
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button
          type="button"
          disabled={loading || failed || setModerators.isPending}
          onClick={save}
        >
          {setModerators.isPending && <Spinner data-icon="inline-start" />}
          Zapisz
        </Button>
      </DialogFooter>
    </div>
  );
}
