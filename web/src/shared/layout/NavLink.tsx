"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

type NavLinkProps = {
  href: string;
  className?: string;
  onClick?: () => void;
  children: ReactNode;
};

export function NavLink({ href, className, onClick, children }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <Link
      href={href}
      onClick={onClick}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "rounded-md font-medium hover:bg-accent",
        isActive && "bg-accent underline underline-offset-4",
        className,
      )}
    >
      {children}
    </Link>
  );
}
