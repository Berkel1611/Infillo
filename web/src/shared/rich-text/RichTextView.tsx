"use client";

import { EditorContent, type JSONContent, useEditor } from "@tiptap/react";
import { useEffect, useMemo } from "react";

import { cn } from "@/shared/lib/utils";

import { richTextExtensions } from "./extensions";
import { normalizeDocument } from "./normalize";

type RichTextViewProps = { content: JSONContent; className?: string };

/**
 * Read-only document. TipTap renders it from its schema (no raw HTML anywhere),
 * so a node outside the schema is dropped instead of executed.
 */
export function RichTextView({ content, className }: RichTextViewProps) {
  const safe = useMemo(() => normalizeDocument(content), [content]);
  const editor = useEditor({
    extensions: richTextExtensions(),
    content: safe,
    editable: false,
    // ProseMirror marks its root as a textbox; a read-only description is plain content
    editorProps: { attributes: { role: "document" } },
    // Next.js renders client components on the server too; TipTap must wait for the browser
    immediatelyRender: false,
  });

  // useEditor uses `content` only when it creates the editor. When the product is saved and
  // refetched, the editor has to be told about the new document, or the old text stays on screen.
  useEffect(() => {
    editor?.commands.setContent(safe, { emitUpdate: false });
  }, [editor, safe]);

  return (
    <EditorContent editor={editor} className={cn("rich-text", className)} />
  );
}
