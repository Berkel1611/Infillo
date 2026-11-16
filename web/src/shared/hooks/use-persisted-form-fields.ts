"use client";

import { useCallback, useEffect } from "react";
import type {
  FieldValues,
  Path,
  PathValue,
  UseFormReturn,
} from "react-hook-form";

const PREFIX = "infillo:form:";

function readStored(key: string): Record<string, unknown> {
  try {
    const raw = window.sessionStorage.getItem(PREFIX + key);
    const data: unknown = raw ? JSON.parse(raw) : null;
    return data && typeof data === "object"
      ? (data as Record<string, unknown>)
      : {};
  } catch {
    // Storage blocked (private mode) or broken JSON: start with an empty form
    return {};
  }
}

/**
 * Remembers what the user typed in sessionStorage, so a page reload (e.g. after a
 * failed login) does not lose it. Fields listed in `skip` (passwords) are never stored.
 * `skip` must be a stable value (a constant outside the component).
 */
export function usePersistedFormFields<T extends FieldValues>(
  key: string,
  form: UseFormReturn<T>,
  skip: readonly Path<T>[],
) {
  const { setValue, watch } = form;

  useEffect(() => {
    // Restore after mount (sessionStorage does not exist on the server)
    for (const [name, value] of Object.entries(readStored(key))) {
      if (skip.includes(name as Path<T>) || typeof value !== "string") {
        continue;
      }
      setValue(name as Path<T>, value as PathValue<T, Path<T>>);
    }

    // Save on every change
    const subscription = watch((values) => {
      const data = Object.fromEntries(
        Object.entries(values).filter(
          ([name]) => !skip.includes(name as Path<T>),
        ),
      );
      try {
        window.sessionStorage.setItem(PREFIX + key, JSON.stringify(data));
      } catch {
        // Storage blocked or full: the fields just will not be remembered
      }
    });
    return () => subscription.unsubscribe();
  }, [key, setValue, watch, skip]);

  /** Call after a successful submit, so the next visit starts with an empty form. */
  const clear = useCallback(() => {
    try {
      window.sessionStorage.removeItem(PREFIX + key);
    } catch {
      // Nothing to clear
    }
  }, [key]);

  return { clear };
}
