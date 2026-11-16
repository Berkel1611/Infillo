import type { Metadata } from "next";

import { AccountPage } from "@/features/account/components/AccountPage";

export const metadata: Metadata = { title: "Konto" };

export default function AccountRoute() {
  return <AccountPage />;
}
