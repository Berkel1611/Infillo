"use client";

import { CloudAlertIcon } from "@hugeicons/core-free-icons";
import { useEffect, useId, useState } from "react";
import { toast } from "sonner";

import { roleLabels } from "@/features/auth/roles";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { useUpdateUser, useUsers } from "../hooks";
import {
  PAGE_SIZE,
  type RoleFilter,
  type UserChange,
  type UsersQuery,
} from "../types";
import { type PendingAction, UserConfirmDialog } from "./UserConfirmDialog";
import { UsersTable } from "./UsersTable";

const INITIAL_QUERY: UsersQuery = { role: "", search: "", page: 1 };
const SEARCH_DELAY_MS = 300;

export function UsersPage() {
  const roleId = useId();
  const searchId = useId();
  const [query, setQuery] = useState<UsersQuery>(INITIAL_QUERY);
  const [searchInput, setSearchInput] = useState("");
  const [pending, setPending] = useState<PendingAction | null>(null);
  const { data, isPending, isError, isPlaceholderData, refetch } =
    useUsers(query);
  const updateUser = useUpdateUser();

  // Search as you type, but ask the API only after a short pause
  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery((q) =>
        q.search === searchInput ? q : { ...q, search: searchInput, page: 1 },
      );
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [searchInput]);

  function confirm() {
    if (!pending) {
      return;
    }
    const { user, action } = pending;
    const change: UserChange =
      action === "role"
        ? { role: user.role === "moderator" ? "user" : "moderator" }
        : { is_active: !user.is_active };

    updateUser.mutate(
      { id: user.id, change },
      {
        onSuccess: () => {
          toast.success(`Zapisano zmiany: ${user.username}.`);
          setPending(null);
          // The role filter can remove the last row of this page: go one page back,
          // because the API answers 404 for a page that does not exist
          if (
            action === "role" &&
            query.role !== "" &&
            data?.results.length === 1 &&
            query.page > 1
          ) {
            setQuery((q) => ({ ...q, page: q.page - 1 }));
          }
        },
        onError: (error) => {
          toast.error(errorMessage(error));
          setPending(null);
        },
      },
    );
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8">
      <h1 className="text-3xl font-semibold">Użytkownicy</h1>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <div className="flex flex-col gap-2 sm:w-56">
          <Label htmlFor={roleId}>Rola</Label>
          <select
            id={roleId}
            value={query.role}
            onChange={(event) =>
              setQuery((q) => ({
                ...q,
                role: event.target.value as RoleFilter,
                page: 1,
              }))
            }
            className="h-9 w-full rounded-4xl border border-input bg-input/30 px-3 text-base outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 md:text-sm"
          >
            <option value="">Wszystkie role</option>
            <option value="user">{roleLabels.user}</option>
            <option value="moderator">{roleLabels.moderator}</option>
            <option value="admin">{roleLabels.admin}</option>
          </select>
        </div>
        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor={searchId}>Szukaj po e-mailu</Label>
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
          title="Nie udało się wczytać użytkowników"
          description="Sprawdź połączenie i spróbuj ponownie."
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
            Liczba kont: {data.count}
          </p>

          {data.results.length === 0 ? (
            <p className="py-12 text-center text-muted-foreground">
              Brak kont pasujących do filtrów.
            </p>
          ) : (
            <UsersTable
              users={data.results}
              onAction={(user, action) => setPending({ user, action })}
            />
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

      <UserConfirmDialog
        pending={pending}
        isSaving={updateUser.isPending}
        onConfirm={confirm}
        onClose={() => setPending(null)}
      />
    </div>
  );
}
