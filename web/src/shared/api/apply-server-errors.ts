import type { FieldValues, Path, UseFormSetError } from "react-hook-form";

import { ApiError } from "./client";
import { errorMessage, fieldErrorMessage } from "./error-messages";

// Errors the API reports with a code, but which belong to one field (HTTP 409)
const CODE_FIELDS: Record<string, string> = {
  EMAIL_TAKEN: "email",
  USERNAME_TAKEN: "username",
  CATEGORY_NAME_TAKEN: "name",
};

/**
 * Puts the server's errors next to the form fields they belong to.
 * Returns true when at least one error was placed on a field; otherwise the
 * caller shows a general alert.
 */
export function applyServerErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  formFields: readonly Path<T>[],
): boolean {
  if (!(error instanceof ApiError)) {
    return false;
  }
  const known = new Set<string>(formFields);
  const placed = new Set<string>();

  function place(field: string, message: string) {
    // Unknown field or a second error on the same field: ignore
    if (!known.has(field) || placed.has(field)) {
      return;
    }
    // Focus goes to the first field with an error (keyboard users)
    setError(
      field as Path<T>,
      { type: "server", message },
      { shouldFocus: placed.size === 0 },
    );
    placed.add(field);
  }

  const codeField = CODE_FIELDS[error.code];
  if (codeField) {
    place(codeField, errorMessage(error));
  }
  for (const { field, type } of error.fields) {
    place(field, fieldErrorMessage(type));
  }
  return placed.size > 0;
}
