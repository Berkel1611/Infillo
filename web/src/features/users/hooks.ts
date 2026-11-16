import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { usersApi } from "./api";
import type { UserChange, UsersQuery } from "./types";

export function useUsers(query: UsersQuery) {
  return useQuery({
    queryKey: ["users", query],
    queryFn: () => usersApi.list(query),
    // The previous page stays on screen while the next one loads
    placeholderData: keepPreviousData,
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, change }: { id: number; change: UserChange }) =>
      usersApi.update(id, change),
    // Returned promise: the mutation lasts until the list is refreshed
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });
}
