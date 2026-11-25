"use client";

import { Tick02Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useId } from "react";

import { Button } from "@/shared/ui/button";

import {
  type AttributeKey,
  isOptionAvailable,
  type OptionGroup,
  type Selection,
} from "../variant-options";
import type { Variant } from "../types";

/** Up to this many options a group is shown as tiles; more of them go into a list. */
const MAX_TILES = 6;

type VariantSelectorProps = {
  variants: Variant[];
  groups: OptionGroup[];
  /** The effective selection (see effectiveSelection). */
  selection: Selection;
  hasUserChoice: boolean;
  onChange: (key: AttributeKey, value: string) => void;
  onClear: () => void;
};

/**
 * One group of choices per attribute (size, color, material). Tiles are native radio buttons:
 * Tab enters a group, arrow keys move inside it, Space selects, and a screen reader announces
 * the group name and the state. A combination that does not exist is disabled, not hidden.
 */
export function VariantSelector({
  variants,
  groups,
  selection,
  hasUserChoice,
  onChange,
  onClear,
}: VariantSelectorProps) {
  if (groups.length === 0) {
    return null; // a single, unnamed variant: nothing to choose
  }

  return (
    <div className="flex flex-col gap-4">
      {groups.map((group) =>
        group.options.length > MAX_TILES ? (
          <SelectGroup
            key={group.key}
            group={group}
            variants={variants}
            selection={selection}
            onChange={onChange}
          />
        ) : (
          <TileGroup
            key={group.key}
            group={group}
            variants={variants}
            selection={selection}
            onChange={onChange}
          />
        ),
      )}
      {hasUserChoice && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="w-fit"
          onClick={onClear}
        >
          Wyczyść wybór
        </Button>
      )}
    </div>
  );
}

type GroupProps = Pick<
  VariantSelectorProps,
  "variants" | "selection" | "onChange"
> & { group: OptionGroup };

const optionText = (group: OptionGroup, option: string) =>
  option === "" ? group.empty : option;

function TileGroup({ group, variants, selection, onChange }: GroupProps) {
  const name = useId();

  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-2 text-sm font-medium">{group.label}</legend>
      <div className="flex flex-wrap gap-2">
        {group.options.map((option) => {
          const available = isOptionAvailable(
            variants,
            selection,
            group.key,
            option,
          );
          return (
            <label
              key={option}
              title={
                available ? undefined : "Brak takiej kombinacji z Twoim wyborem"
              }
              className="group flex cursor-pointer items-center gap-1 rounded-lg border bg-card px-3 py-1.5 text-sm font-medium hover:bg-accent has-checked:border-primary has-checked:bg-primary has-checked:text-primary-foreground has-focus-visible:ring-3 has-focus-visible:ring-ring/50 has-disabled:cursor-not-allowed has-disabled:line-through has-disabled:opacity-50 has-disabled:hover:bg-card"
            >
              <input
                type="radio"
                name={name}
                value={option}
                checked={selection[group.key] === option}
                disabled={!available}
                onChange={() => onChange(group.key, option)}
                className="sr-only"
              />
              <HugeiconsIcon
                icon={Tick02Icon}
                aria-hidden
                className="hidden size-3.5 group-has-checked:block"
              />
              {optionText(group, option)}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function SelectGroup({ group, variants, selection, onChange }: GroupProps) {
  const id = useId();

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium">
        {group.label}
      </label>
      <select
        id={id}
        value={selection[group.key] ?? ""}
        onChange={(event) => onChange(group.key, event.target.value)}
        className="h-9 w-full rounded-4xl border border-input bg-input/30 px-3 text-base outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 md:text-sm"
      >
        <option value="" disabled>
          Wybierz
        </option>
        {group.options.map((option) => (
          <option
            key={option}
            value={option}
            disabled={
              !isOptionAvailable(variants, selection, group.key, option)
            }
          >
            {optionText(group, option)}
          </option>
        ))}
      </select>
    </div>
  );
}
