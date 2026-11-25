"use client";

import {
  FolderLibraryIcon,
  Logout01Icon,
  Package01Icon,
  ShieldUserIcon,
  UserSettings01Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import Link from "next/link";
import { toast } from "sonner";

import { errorMessage } from "@/shared/api/error-messages";
import { Avatar, AvatarFallback } from "@/shared/ui/avatar";
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";

import { useCurrentUser, useLogout } from "../hooks";
import { roleLabels } from "../roles";

export function UserMenu() {
  const { data: user, isPending } = useCurrentUser();
  const logout = useLogout();

  if (isPending) {
    // Keeps the place, so the header does not jump when the user loads
    return <div aria-hidden className="h-9 w-24" />;
  }
  if (!user) {
    return (
      <Button
        variant="outline"
        render={<Link href="/login" />}
        nativeButton={false}
      >
        Zaloguj się
      </Button>
    );
  }

  const initials = `${user.first_name[0] ?? ""}${user.last_name[0] ?? ""}`;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={<Button variant="ghost" className="gap-2 px-2" />}
        aria-label={`Menu użytkownika: ${user.username}`}
      >
        <Avatar>
          <AvatarFallback>{initials.toUpperCase()}</AvatarFallback>
        </Avatar>
        <span className="hidden max-w-32 truncate sm:inline">
          {user.username}
        </span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuGroup>
          <DropdownMenuLabel>
            <span className="block truncate text-sm text-foreground">
              {user.username}
            </span>
            <span className="block font-normal">{roleLabels[user.role]}</span>
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem render={<Link href="/account" />}>
          <HugeiconsIcon icon={UserSettings01Icon} aria-hidden />
          Konto
        </DropdownMenuItem>
        {(user.role === "moderator" || user.role === "admin") && (
          <DropdownMenuItem render={<Link href="/manage/products" />}>
            <HugeiconsIcon icon={Package01Icon} aria-hidden />
            Moje produkty
          </DropdownMenuItem>
        )}
        {user.role === "admin" && (
          <>
            <DropdownMenuItem render={<Link href="/admin/categories" />}>
              <HugeiconsIcon icon={FolderLibraryIcon} aria-hidden />
              Kategorie
            </DropdownMenuItem>
            <DropdownMenuItem render={<Link href="/admin/users" />}>
              <HugeiconsIcon icon={ShieldUserIcon} aria-hidden />
              Panel administratora
            </DropdownMenuItem>
          </>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() =>
            logout.mutate(undefined, {
              onError: (error) => toast.error(errorMessage(error)),
            })
          }
        >
          <HugeiconsIcon icon={Logout01Icon} aria-hidden />
          Wyloguj
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
