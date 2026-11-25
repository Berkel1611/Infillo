import type { JSONContent } from "@tiptap/react";

/** The only rel the server accepts for a link that opens in a new tab (see rich_text.py). */
const LINK_REL = "noopener noreferrer";

function normalizeMark(mark: NonNullable<JSONContent["marks"]>[number]) {
  if (mark.type !== "link") {
    return mark;
  }
  // Whatever came in (a pasted <a target="_self" title="...">, an old document), a link
  // always opens in a new tab with noopener and carries no class or title
  return {
    ...mark,
    attrs: {
      href: mark.attrs?.href,
      target: "_blank",
      rel: LINK_REL,
      class: null,
      title: null,
    },
  };
}

/**
 * Returns the document with every link's attributes forced to the safe, accepted values.
 * Used before a document is sent to the server and before it is shown, so neither a pasted
 * link nor a stored document can bring its own `rel` (tabnabbing) or `class` into the page.
 */
export function normalizeDocument(doc: JSONContent): JSONContent {
  return {
    ...doc,
    ...(doc.marks && { marks: doc.marks.map(normalizeMark) }),
    ...(doc.content && { content: doc.content.map(normalizeDocument) }),
  };
}
