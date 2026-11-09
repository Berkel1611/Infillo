import Link from "next/link";
import type { ReactNode } from "react";

import { MobileNav } from "./MobileNav";
import { NAV_ITEMS } from "./nav-items";
import { NavLink } from "./NavLink";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Przejdź do treści
      </a>
      <header className="border-b bg-card">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
          <Link href="/" className="rounded-md text-xl font-semibold">
            Infillo
          </Link>

          <nav aria-label="Główna" className="hidden md:block">
            <ul className="flex gap-1">
              {NAV_ITEMS.map((item) => (
                <li key={item.href}>
                  <NavLink href={item.href} className="px-3 py-2">
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <MobileNav />
        </div>
      </header>
      <main id="main" tabIndex={-1} className="flex-1 outline-none">
        {children}
      </main>

      <footer className="border-t bg-card">
        <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-muted-foreground">
          © 2026 Infillo
        </div>
      </footer>
    </>
  );
}
