import type { JSONContent } from "@tiptap/react";

/** True when the document has no text other than whitespace (the server uses the same rule). */
export function isEmptyDocument(doc: JSONContent | null | undefined): boolean {
  if (!doc) {
    return true;
  }
  if (typeof doc.text === "string" && doc.text.trim() !== "") {
    return false;
  }
  return (doc.content ?? []).every(isEmptyDocument);
}
