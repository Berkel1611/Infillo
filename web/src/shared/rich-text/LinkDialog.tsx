"use client";

import { useState } from "react";

import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";

type LinkDialogProps = {
  /** Current address of the link ("" for a new one); null when the dialog is closed. */
  href: string | null;
  onClose: () => void;
  onSave: (href: string) => void;
  onRemove: () => void;
};

/** Adds https:// when missing; null when it is not a web address. Only http(s) is allowed. */
export function normalizeHref(value: string): string | null {
  const trimmed = value.trim();
  const withProtocol = /^https?:\/\//i.test(trimmed)
    ? trimmed
    : `https://${trimmed}`;
  try {
    const url = new URL(withProtocol);
    return url.hostname.includes(".") ? url.href : null;
  } catch {
    return null;
  }
}

export function LinkDialog({
  href,
  onClose,
  onSave,
  onRemove,
}: LinkDialogProps) {
  return (
    <Dialog
      open={href !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent>
        {href !== null && (
          <LinkForm href={href} onSave={onSave} onRemove={onRemove} />
        )}
      </DialogContent>
    </Dialog>
  );
}

function LinkForm({
  href,
  onSave,
  onRemove,
}: Omit<LinkDialogProps, "onClose"> & { href: string }) {
  const [value, setValue] = useState(href);
  const [error, setError] = useState<string>();

  return (
    <form
      noValidate
      className="grid gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        // The dialog is portaled, but React still bubbles the submit event up to the form
        // around the editor (e.g. the product form), which must not be submitted by it
        event.stopPropagation();
        const normalized = normalizeHref(value);
        if (!normalized) {
          setError("Wpisz adres strony, np. https://example.com.");
          return;
        }
        onSave(normalized);
      }}
    >
      <DialogHeader>
        <DialogTitle>{href ? "Edycja linku" : "Nowy link"}</DialogTitle>
      </DialogHeader>
      <FormField label="Adres strony" error={error}>
        {(control) => (
          <Input
            {...control}
            type="url"
            value={value}
            autoComplete="off"
            placeholder="https://"
            onChange={(event) => {
              setValue(event.target.value);
              setError(undefined);
            }}
          />
        )}
      </FormField>
      <DialogFooter>
        {href && (
          <Button
            type="button"
            variant="destructive"
            className="sm:mr-auto"
            onClick={onRemove}
          >
            Usuń link
          </Button>
        )}
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button type="submit">Zapisz</Button>
      </DialogFooter>
    </form>
  );
}
