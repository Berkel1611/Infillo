"use client";

import { EditorContent, type JSONContent, useEditor } from "@tiptap/react";
import { useLayoutEffect, useRef, useState } from "react";

import { cn } from "@/shared/lib/utils";
import type { FieldControlProps } from "@/shared/ui/form-field";

import { richTextExtensions } from "./extensions";
import { LinkDialog } from "./LinkDialog";
import { RichTextToolbar } from "./RichTextToolbar";

type RichTextEditorProps = Partial<FieldControlProps> & {
  /** Accessible name: <label for> does not name a contenteditable element. */
  label: string;
  /** Content when the editor mounts; later changes come only from the editor. */
  initialContent: JSONContent | null;
  onChange: (doc: JSONContent) => void;
  className?: string;
};

export function RichTextEditor({
  initialContent,
  onChange,
  className,
  label,
  id,
  "aria-invalid": invalid,
  "aria-describedby": describedBy,
}: RichTextEditorProps) {
  const [linkHref, setLinkHref] = useState<string | null>(null);
  // The editor is created once; the ref makes it always call the latest callback
  const onChangeRef = useRef(onChange);
  useLayoutEffect(() => {
    onChangeRef.current = onChange;
  });

  const editor = useEditor({
    extensions: richTextExtensions(),
    content: initialContent ?? "",
    // Next.js renders client components on the server too; TipTap must wait for the browser
    immediatelyRender: false,
    editorProps: {
      attributes: {
        ...(id && { id }),
        ...(invalid && { "aria-invalid": "true" }),
        ...(describedBy && { "aria-describedby": describedBy }),
        "aria-label": label,
        role: "textbox",
        "aria-multiline": "true",
        class: "rich-text min-h-40 px-4 py-3 text-base outline-none",
      },
    },
    onUpdate: ({ editor: e }) => onChangeRef.current(e.getJSON()),
  });

  if (!editor) {
    // Same height as the real editor, so the page does not jump when it appears
    return <div className={cn("min-h-52 rounded-lg border", className)} />;
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-input focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50 has-aria-invalid:border-destructive",
        className,
      )}
    >
      <RichTextToolbar
        editor={editor}
        onLink={() => setLinkHref(editor.getAttributes("link").href ?? "")}
      />
      <EditorContent editor={editor} />

      <LinkDialog
        href={linkHref}
        onClose={() => {
          setLinkHref(null);
          editor.chain().focus().run();
        }}
        onSave={(href) => {
          const chain = editor.chain().focus().extendMarkRange("link");
          if (editor.state.selection.empty && !editor.isActive("link")) {
            // No selected text: insert the address itself as the link text
            chain
              .insertContent({
                type: "text",
                text: href,
                marks: [{ type: "link", attrs: { href } }],
              })
              .run();
          } else {
            chain.setLink({ href }).run();
          }
          setLinkHref(null);
        }}
        onRemove={() => {
          editor.chain().focus().extendMarkRange("link").unsetLink().run();
          setLinkHref(null);
        }}
      />
    </div>
  );
}
