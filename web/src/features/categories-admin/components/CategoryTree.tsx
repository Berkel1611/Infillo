"use client";

import {
  Add01Icon,
  Delete02Icon,
  Edit02Icon,
  UserGroupIcon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

import { MAX_CATEGORY_DEPTH } from "@/features/catalog/category-labels";
import type { CategoryNode } from "@/features/catalog/types";
import { Button } from "@/shared/ui/button";

export type CategoryAction = "add" | "edit" | "moderators" | "delete";

type CategoryTreeProps = {
  nodes: CategoryNode[];
  /** 1 = the roots. */
  depth?: number;
  /** `trigger` is the clicked button: the page returns the focus to it when a dialog closes. */
  onAction: (action: CategoryAction, id: number, trigger: HTMLElement) => void;
};

/**
 * Categories as nested lists with plain buttons: every button is a tab stop and works with
 * Enter and Space; no custom "tree" widget with its own arrow-key model is needed.
 * Each button names its category (aria-label), because "Usuń" alone says nothing out of context.
 */
export function CategoryTree({
  nodes,
  depth = 1,
  onAction,
}: CategoryTreeProps) {
  return (
    <ul className="flex flex-col gap-1">
      {nodes.map((node) => (
        <li key={node.id}>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg px-2 py-1 hover:bg-accent">
            <span className="min-w-0 flex-1 font-medium break-words">
              {node.name}
            </span>
            <div className="flex flex-wrap gap-1">
              {depth < MAX_CATEGORY_DEPTH && (
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={`Dodaj podkategorię w: ${node.name}`}
                  onClick={(event) =>
                    onAction("add", node.id, event.currentTarget)
                  }
                >
                  <HugeiconsIcon icon={Add01Icon} aria-hidden />
                  Podkategoria
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                aria-label={`Zmień nazwę lub przenieś: ${node.name}`}
                onClick={(event) =>
                  onAction("edit", node.id, event.currentTarget)
                }
              >
                <HugeiconsIcon icon={Edit02Icon} aria-hidden />
                Edytuj
              </Button>
              <Button
                variant="ghost"
                size="sm"
                aria-label={`Przydziel moderatorów do: ${node.name}`}
                onClick={(event) =>
                  onAction("moderators", node.id, event.currentTarget)
                }
              >
                <HugeiconsIcon icon={UserGroupIcon} aria-hidden />
                Moderatorzy
              </Button>
              <Button
                variant="ghost"
                size="sm"
                aria-label={`Usuń kategorię: ${node.name}`}
                onClick={(event) =>
                  onAction("delete", node.id, event.currentTarget)
                }
              >
                <HugeiconsIcon icon={Delete02Icon} aria-hidden />
                Usuń
              </Button>
            </div>
          </div>
          {node.children.length > 0 && (
            <div className="ml-4 border-l pl-3 sm:ml-6 sm:pl-4">
              <CategoryTree
                nodes={node.children}
                depth={depth + 1}
                onAction={onAction}
              />
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
