"use client";

import { CloudAlertIcon } from "@hugeicons/core-free-icons";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { flattenTree } from "@/features/catalog/category-labels";
import { useCategories, useDeleteCategory } from "@/features/catalog/hooks";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import {
  CategoryFormDialog,
  type CategoryFormTarget,
} from "./CategoryFormDialog";
import { type CategoryAction, CategoryTree } from "./CategoryTree";
import { ModeratorAssignDialog } from "./ModeratorAssignDialog";

/** One dialog is open at a time; the value says which one and for which category. */
type OpenDialog =
  | { type: "form"; target: CategoryFormTarget }
  | { type: "moderators"; id: number }
  | { type: "delete"; id: number }
  | null;

export function CategoriesAdminPage() {
  const { data: tree, isPending, error, refetch } = useCategories();
  const deleteCategory = useDeleteCategory();
  const [dialog, setDialog] = useState<OpenDialog>(null);
  // The button that opened the dialog. Dialogs are opened from state, not through a trigger
  // element, so the focus would be lost on close; this puts it back (see returnFocus below).
  const opener = useRef<HTMLElement | null>(null);
  const addRootButton = useRef<HTMLButtonElement>(null);

  // A failed refresh (e.g. after saving) must not hide the tree that is already loaded
  if (tree === undefined) {
    return isPending ? (
      <PageSpinner />
    ) : (
      <PageMessage
        icon={CloudAlertIcon}
        title="Nie udało się wczytać kategorii"
        description={errorMessage(error)}
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  const entries = flattenTree(tree);
  const byId = new Map(entries.map((entry) => [entry.id, entry]));
  const close = () => setDialog(null);

  // Back to the opener; when it is gone (the category was deleted), to the first button
  const returnFocus = () =>
    opener.current?.isConnected ? opener.current : addRootButton.current;

  function onAction(action: CategoryAction, id: number, trigger: HTMLElement) {
    opener.current = trigger;
    if (action === "add") {
      setDialog({ type: "form", target: { mode: "create", parentId: id } });
    } else if (action === "edit") {
      setDialog({ type: "form", target: { mode: "edit", id } });
    } else if (action === "moderators") {
      setDialog({ type: "moderators", id });
    } else {
      setDialog({ type: "delete", id });
    }
  }

  const moderatorsFor =
    dialog?.type === "moderators" ? byId.get(dialog.id) : undefined;
  const toDelete = dialog?.type === "delete" ? byId.get(dialog.id) : undefined;

  function confirmDelete() {
    if (!toDelete) {
      return;
    }
    deleteCategory.mutate(toDelete.id, {
      onSuccess: () => {
        toast.success(`Usunięto kategorię: ${toDelete.name}.`);
        close();
      },
      onError: (error) => {
        // e.g. CATEGORY_NOT_EMPTY: the category still has subcategories or products
        toast.error(errorMessage(error));
        close();
      },
    });
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold">Kategorie</h1>
        <Button
          ref={addRootButton}
          onClick={(event) => {
            opener.current = event.currentTarget;
            setDialog({
              type: "form",
              target: { mode: "create", parentId: null },
            });
          }}
        >
          Dodaj kategorię główną
        </Button>
      </div>
      <p className="text-muted-foreground">
        Kategorie mogą mieć najwyżej trzy poziomy. Moderator przydzielony do
        kategorii zarządza też produktami w jej podkategoriach.
      </p>

      {tree.length === 0 ? (
        <p className="py-8 text-center text-muted-foreground">
          Nie ma jeszcze żadnych kategorii.
        </p>
      ) : (
        <CategoryTree nodes={tree} onAction={onAction} />
      )}

      <CategoryFormDialog
        target={dialog?.type === "form" ? dialog.target : null}
        entries={entries}
        finalFocus={returnFocus}
        onClose={close}
      />
      <ModeratorAssignDialog
        category={
          moderatorsFor
            ? { id: moderatorsFor.id, name: moderatorsFor.name }
            : null
        }
        finalFocus={returnFocus}
        onClose={close}
      />
      <AlertDialog
        open={toDelete !== undefined}
        onOpenChange={(open) => {
          if (!open) {
            close();
          }
        }}
      >
        <AlertDialogContent finalFocus={returnFocus}>
          <AlertDialogHeader>
            <AlertDialogTitle>Usunąć kategorię?</AlertDialogTitle>
            <AlertDialogDescription>
              Kategoria „{toDelete?.name}” zostanie usunięta. Nie można usunąć
              kategorii, która ma podkategorie lub produkty.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={deleteCategory.isPending}
              onClick={confirmDelete}
            >
              {deleteCategory.isPending && <Spinner data-icon="inline-start" />}
              Usuń
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
