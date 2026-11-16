import { api } from "@/shared/api/client";
import type { User } from "@/features/auth/types";

import type { UserChange, UserPage, UsersQuery } from "./types";

export const usersApi = {
  list: ({ role, search, page }: UsersQuery) => {
    const params = new URLSearchParams({ page: String(page) });
    if (role) {
      params.set("role", role);
    }
    if (search.trim()) {
      params.set("search", search.trim());
    }
    return api.get<UserPage>(`/users?${params}`);
  },
  update: (id: number, change: UserChange) =>
    api.patch<User>(`/users/${id}`, change),
};
