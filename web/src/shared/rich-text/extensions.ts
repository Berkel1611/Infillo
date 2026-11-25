import type { Extensions } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

/**
 * One schema for editing and reading. It must stay identical to the allowlist of the
 * backend validator (api/apps/catalog/rich_text.py):
 *   nodes: paragraph, heading (level 2-3), bulletList, orderedList, listItem, hardBreak
 *   marks: bold, italic, link (http / https only)
 * Everything else in StarterKit is switched off, so the editor cannot produce it and
 * a document that contains it is not rendered.
 */
export function richTextExtensions(): Extensions {
  return [
    StarterKit.configure({
      heading: { levels: [2, 3] },
      blockquote: false,
      code: false,
      codeBlock: false,
      horizontalRule: false,
      strike: false,
      underline: false,
      link: {
        openOnClick: false,
        autolink: true,
        defaultProtocol: "https",
        // The server accepts only http(s) links, so do not create any other kind
        isAllowedUri: (url) => /^https?:\/\//i.test(url),
        HTMLAttributes: { target: "_blank", rel: "noopener noreferrer" },
      },
    }),
  ];
}
