"use client";

import { useCurrentUser } from "@/features/auth/hooks";

import { AddressForm } from "./AddressForm";
import { ProfileForm } from "./ProfileForm";

export function AccountPage() {
  // Inside AuthGuard, so the user is already loaded
  const { data: user } = useCurrentUser();
  if (!user) {
    return null;
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-8">
      <h1 className="text-3xl font-semibold">Konto</h1>
      <ProfileForm user={user} />
      <AddressForm />
    </div>
  );
}
