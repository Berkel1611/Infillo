import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { currentUserKey } from "@/features/auth/hooks";

import { accountApi } from "./api";

const addressKey = ["account", "address"] as const;

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: accountApi.updateProfile,
    // The header menu reads the same cached user
    onSuccess: (user) => queryClient.setQueryData(currentUserKey, user),
  });
}

export function useAddress() {
  return useQuery({ queryKey: addressKey, queryFn: accountApi.getAddress });
}

export function useSaveAddress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: accountApi.saveAddress,
    onSuccess: (address) => queryClient.setQueryData(addressKey, address),
  });
}
