"use client";

import { FilterHorizontalIcon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import Link from "next/link";
import { useId, useState } from "react";

import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";

import type { CategoryNode } from "../types";
import { productsHref } from "../urls";

type LinkContext = {
  selected: number | null;
  /** Kept in the links, so choosing a category does not forget the search. */
  search: string;
  onNavigate: () => void;
};

function CategoryLink({
  id,
  name,
  context,
}: {
  id: number | null;
  name: string;
  context: LinkContext;
}) {
  const current = id === context.selected;
  return (
    <Link
      href={productsHref({ category: id, search: context.search })}
      aria-current={current ? "page" : undefined}
      onClick={context.onNavigate}
      className={cn(
        "block rounded-lg px-3 py-1.5 hover:bg-accent",
        current && "bg-accent font-semibold underline underline-offset-4",
      )}
    >
      {name}
    </Link>
  );
}

function Branch({
  nodes,
  context,
}: {
  nodes: CategoryNode[];
  context: LinkContext;
}) {
  return (
    <ul className="flex flex-col gap-0.5">
      {nodes.map((node) => (
        <li key={node.id}>
          <CategoryLink id={node.id} name={node.name} context={context} />
          {node.children.length > 0 && (
            <div className="ml-3 border-l pl-1">
              <Branch nodes={node.children} context={context} />
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}

type CategoryFilterProps = {
  tree: CategoryNode[];
  selected: number | null;
  search: string;
};

/**
 * Categories as nested lists of links: every link is a plain tab stop, Enter follows it,
 * and the current one has aria-current. From the md breakpoint up the list is always
 * visible; below it a button opens and closes it.
 */
export function CategoryFilter({
  tree,
  selected,
  search,
}: CategoryFilterProps) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const context: LinkContext = {
    selected,
    search,
    onNavigate: () => setOpen(false),
  };

  return (
    <div>
      <Button
        type="button"
        variant="outline"
        className="md:hidden"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        <HugeiconsIcon icon={FilterHorizontalIcon} aria-hidden />
        Kategorie
      </Button>
      <nav
        id={panelId}
        aria-label="Kategorie"
        className={cn("mt-2 md:mt-0 md:block", open ? "block" : "hidden")}
      >
        <ul className="flex flex-col gap-0.5">
          <li>
            <CategoryLink
              id={null}
              name="Wszystkie produkty"
              context={context}
            />
          </li>
          <li>
            <Branch nodes={tree} context={context} />
          </li>
        </ul>
      </nav>
    </div>
  );
}
