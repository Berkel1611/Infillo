"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, Suspense } from "react";

import { cn } from "@/shared/lib/utils";

type NavLinkProps = {
  href: string;
  className?: string;
  onClick?: () => void;
  children: ReactNode;
};

const baseClass = "rounded-md font-medium hover:bg-accent";

/**
 * Link of the main navigation with aria-current on the current section.
 * usePathname() suspends on routes whose params are unknown at build time (e.g. /products/[id]),
 * so the part that reads it sits in Suspense; the fallback is the same link without the highlight.
 */
export function NavLink({ href, className, onClick, children }: NavLinkProps) {
  return (
    <Suspense
      fallback={
        <Link
          href={href}
          onClick={onClick}
          className={cn(baseClass, className)}
        >
          {children}
        </Link>
      }
    >
      <CurrentAwareLink href={href} className={className} onClick={onClick}>
        {children}
      </CurrentAwareLink>
    </Suspense>
  );
}

function CurrentAwareLink({
  href,
  className,
  onClick,
  children,
}: NavLinkProps) {
  const pathname = usePathname();
  const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <Link
      href={href}
      onClick={onClick}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        baseClass,
        isActive && "bg-accent underline underline-offset-4",
        className,
      )}
    >
      {children}
    </Link>
  );
}
