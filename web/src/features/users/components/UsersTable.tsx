import type { User } from "@/features/auth/types";
import { roleLabels } from "@/features/auth/roles";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

export type UserAction = "role" | "active";

type UsersTableProps = {
  users: User[];
  onAction: (user: User, action: UserAction) => void;
};

const dateFormat = new Intl.DateTimeFormat("pl-PL", { dateStyle: "medium" });

function StatusBadge({ isActive }: { isActive: boolean }) {
  return (
    <Badge variant={isActive ? "secondary" : "destructive"}>
      {isActive ? "Aktywne" : "Zablokowane"}
    </Badge>
  );
}

function UserActions({
  user,
  onAction,
}: {
  user: User;
  onAction: UsersTableProps["onAction"];
}) {
  // Administrators cannot be changed (the API refuses it too)
  if (user.role === "admin") {
    return (
      <span className="text-muted-foreground">
        <span aria-hidden>—</span>
        <span className="sr-only">Brak dostępnych akcji</span>
      </span>
    );
  }
  const roleText =
    user.role === "moderator"
      ? "Odbierz rolę moderatora"
      : "Nadaj rolę moderatora";
  const activeText = user.is_active ? "Zablokuj" : "Odblokuj";

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onAction(user, "role")}
        aria-label={`${roleText}: ${user.username}`}
      >
        {roleText}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onAction(user, "active")}
        aria-label={`${activeText} konto: ${user.username}`}
      >
        {activeText}
      </Button>
    </div>
  );
}

export function UsersTable({ users, onAction }: UsersTableProps) {
  return (
    <>
      <div className="hidden md:block">
        <Table>
          <TableCaption className="sr-only">Lista użytkowników</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Nazwa użytkownika</TableHead>
              <TableHead>E-mail</TableHead>
              <TableHead>Rola</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Założone</TableHead>
              <TableHead>Akcje</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">{user.username}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{roleLabels[user.role]}</TableCell>
                <TableCell>
                  <StatusBadge isActive={user.is_active} />
                </TableCell>
                <TableCell>
                  {dateFormat.format(new Date(user.date_joined))}
                </TableCell>
                <TableCell>
                  <UserActions user={user} onAction={onAction} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <ul className="flex flex-col gap-3 md:hidden">
        {users.map((user) => (
          <li
            key={user.id}
            className="flex flex-col gap-3 rounded-2xl border bg-card p-4"
          >
            <div>
              <p className="font-medium">{user.username}</p>
              <p className="text-sm break-all text-muted-foreground">
                {user.email}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge variant="outline">{roleLabels[user.role]}</Badge>
              <StatusBadge isActive={user.is_active} />
              <span className="text-muted-foreground">
                od {dateFormat.format(new Date(user.date_joined))}
              </span>
            </div>
            <UserActions user={user} onAction={onAction} />
          </li>
        ))}
      </ul>
    </>
  );
}
