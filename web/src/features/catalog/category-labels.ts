import type { Category, CategoryNode } from "./types";

export type CategoryOption = { id: number; label: string };

/**
 * Flat categories as options with the whole path in the label ("Dom i organizacja › Organizery"),
 * sorted by it, so a subcategory sits right under its parent in a plain <select>.
 */
export function categoryOptions(categories: Category[]): CategoryOption[] {
  const byId = new Map(categories.map((category) => [category.id, category]));

  function label(category: Category): string {
    const parent =
      category.parent_id === null ? undefined : byId.get(category.parent_id);
    return parent ? `${label(parent)} › ${category.name}` : category.name;
  }

  return categories
    .map((category) => ({ id: category.id, label: label(category) }))
    .sort((a, b) => a.label.localeCompare(b.label, "pl"));
}

/** One node of the tree, flattened, with what the admin screens need to know about it. */
export type TreeEntry = {
  id: number;
  name: string;
  parentId: number | null;
  /** 1 = a root category. */
  depth: number;
  /** "Dom i organizacja › Organizery" */
  label: string;
  /** The node itself and everything below it. */
  subtreeIds: number[];
  /** Number of levels below the node: 0 for a leaf. */
  height: number;
};

/** Depth-first, so a parent comes right before its children (the order of the screen). */
export function flattenTree(
  nodes: CategoryNode[],
  depth = 1,
  parent: { id: number; label: string } | null = null,
): TreeEntry[] {
  return nodes.flatMap((node) => {
    const label = parent ? `${parent.label} › ${node.name}` : node.name;
    const below = flattenTree(node.children, depth + 1, { id: node.id, label });
    return [
      {
        id: node.id,
        name: node.name,
        parentId: parent?.id ?? null,
        depth,
        label,
        subtreeIds: [node.id, ...below.map((entry) => entry.id)],
        height:
          below.length === 0
            ? 0
            : Math.max(...below.map((e) => e.depth)) - depth,
      },
      ...below,
    ];
  });
}

/** Mirrors the server rule (services.MAX_CATEGORY_DEPTH): the tree has at most 3 levels. */
export const MAX_CATEGORY_DEPTH = 3;
