import type { Variant } from "./types";

/** The attributes a variant is described by, in the order the groups are shown. */
export const ATTRIBUTES = [
  { key: "size", label: "Rozmiar", empty: "Bez rozmiaru" },
  { key: "color", label: "Kolor", empty: "Bez koloru" },
  { key: "material", label: "Materiał", empty: "Bez materiału" },
] as const;

export type AttributeKey = (typeof ATTRIBUTES)[number]["key"];

/** What the customer has chosen so far; a missing key means "not chosen yet". */
export type Selection = Partial<Record<AttributeKey, string>>;

export type OptionGroup = {
  key: AttributeKey;
  label: string;
  /** Shown for a variant that has no value in this attribute (stored as ""). */
  empty: string;
  /** Distinct values, in the order they first appear among the variants. */
  options: string[];
};

/** One group per attribute that at least one variant uses; an unused attribute is no choice. */
export function optionGroups(variants: Variant[]): OptionGroup[] {
  return ATTRIBUTES.flatMap((attribute) => {
    const options = [...new Set(variants.map((v) => v[attribute.key]))];
    return options.every((option) => option === "")
      ? []
      : [{ ...attribute, options }];
  });
}

/**
 * The selection to work with: only values that still exist (the product may have been edited
 * since the customer chose), and a group with a single option counts as chosen.
 */
export function effectiveSelection(
  groups: OptionGroup[],
  chosen: Selection,
): Selection {
  const result: Selection = {};
  for (const group of groups) {
    const value = chosen[group.key];
    if (value !== undefined && group.options.includes(value)) {
      result[group.key] = value;
    } else if (group.options.length === 1) {
      result[group.key] = group.options[0];
    }
  }
  return result;
}

function matches(variant: Variant, selection: Selection): boolean {
  return ATTRIBUTES.every(
    ({ key }) =>
      selection[key] === undefined || variant[key] === selection[key],
  );
}

/**
 * Can `value` be chosen in group `key` given what is chosen in the other groups?
 * False when no variant has this combination (e.g. no size L in red).
 */
export function isOptionAvailable(
  variants: Variant[],
  selection: Selection,
  key: AttributeKey,
  value: string,
): boolean {
  const others = { ...selection, [key]: value };
  return variants.some((variant) => matches(variant, others));
}

/** The variant the selection points at, or undefined while some group is still open. */
export function resolveVariant(
  variants: Variant[],
  groups: OptionGroup[],
  selection: Selection,
): Variant | undefined {
  if (groups.some((group) => selection[group.key] === undefined)) {
    return undefined;
  }
  return variants.find((variant) => matches(variant, selection));
}

/** Labels of the groups still to choose, e.g. ["rozmiar", "kolor"]. */
export function missingGroupLabels(
  groups: OptionGroup[],
  selection: Selection,
): string[] {
  return groups
    .filter((group) => selection[group.key] === undefined)
    .map((group) => group.label.toLowerCase());
}
