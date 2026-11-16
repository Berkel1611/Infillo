import type { ManagedRole, User, UserRole } from "@/features/auth/types";

export const PAGE_SIZE = 20; // the API default (StandardPagination)

export type RoleFilter = "" | UserRole; // "" = all roles

export type UsersQuery = {
  role: RoleFilter;
  search: string;
  page: number;
};

/** Page of the list: the DRF pagination format. */
export type UserPage = {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
};

/** What an administrator can change: the role or the block. */
export type UserChange = { role: ManagedRole } | { is_active: boolean };
