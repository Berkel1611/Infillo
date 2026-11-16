import type { User } from "@/features/auth/types";
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
import { Spinner } from "@/shared/ui/spinner";

import type { UserAction } from "./UsersTable";

export type PendingAction = { user: User; action: UserAction };

type UserConfirmDialogProps = {
  pending: PendingAction | null; // null = closed
  isSaving: boolean;
  onConfirm: () => void;
  onClose: () => void;
};

function texts({ user, action }: PendingAction) {
  if (action === "role") {
    return user.role === "moderator"
      ? {
          title: "Odebrać rolę moderatora?",
          text: `Konto ${user.username} wróci do roli użytkownika.`,
          confirm: "Odbierz rolę",
          destructive: true,
        }
      : {
          title: "Nadać rolę moderatora?",
          text: `Konto ${user.username} dostanie uprawnienia moderatora.`,
          confirm: "Nadaj rolę",
          destructive: false,
        };
  }
  return user.is_active
    ? {
        title: "Zablokować konto?",
        text: `Konto ${user.username} od razu straci dostęp do sklepu i społeczności.`,
        confirm: "Zablokuj",
        destructive: true,
      }
    : {
        title: "Odblokować konto?",
        text: `Konto ${user.username} znów będzie mogło korzystać ze sklepu i społeczności.`,
        confirm: "Odblokuj",
        destructive: false,
      };
}

export function UserConfirmDialog({
  pending,
  isSaving,
  onConfirm,
  onClose,
}: UserConfirmDialogProps) {
  const content = pending ? texts(pending) : null;

  return (
    <AlertDialog
      open={pending !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <AlertDialogContent>
        {content && (
          <>
            <AlertDialogHeader>
              <AlertDialogTitle>{content.title}</AlertDialogTitle>
              <AlertDialogDescription>{content.text}</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Anuluj</AlertDialogCancel>
              <AlertDialogAction
                variant={content.destructive ? "destructive" : "default"}
                disabled={isSaving}
                onClick={onConfirm}
              >
                {isSaving && <Spinner data-icon="inline-start" />}
                {content.confirm}
              </AlertDialogAction>
            </AlertDialogFooter>
          </>
        )}
      </AlertDialogContent>
    </AlertDialog>
  );
}
