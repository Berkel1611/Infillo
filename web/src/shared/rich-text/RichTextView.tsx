"use client";

import { EditorContent, type JSONContent, useEditor } from "@tiptap/react";

import { cn } from "@/shared/lib/utils";

import { richTextExtensions } from "./extensions";

type RichTextViewProps = { content: JSONContent; className?: string };

/**
 * Read-only document. TipTap renders it from its schema (no raw HTML anywhere),
 * so a node outside the schema is dropped instead of executed.
 */
export function RichTextView({ content, className }: RichTextViewProps) {
  const editor = useEditor({
    extensions: richTextExtensions(),
    content,
    editable: false,
    // ProseMirror marks its root as a textbox; a read-only description is plain content
    editorProps: { attributes: { role: "document" } },
    // Next.js renders client components on the server too; TipTap must wait for the browser
    immediatelyRender: false,
  });

  return (
    <EditorContent editor={editor} className={cn("rich-text", className)} />
  );
}
