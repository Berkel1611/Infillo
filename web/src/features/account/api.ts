import { api } from "@/shared/api/client";
import type { User } from "@/features/auth/types";

import type { ProfileInput, ShippingAddress } from "./types";

export const accountApi = {
  updateProfile: (data: ProfileInput) => api.patch<User>("/auth/me", data),
  // null = no address saved yet
  getAddress: () => api.get<ShippingAddress | null>("/auth/me/address"),
  saveAddress: (data: ShippingAddress) =>
    api.put<ShippingAddress>("/auth/me/address", data),
};
