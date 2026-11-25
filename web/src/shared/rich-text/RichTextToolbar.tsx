"use client";

import {
  Heading02Icon,
  Heading03Icon,
  LeftToRightListBulletIcon,
  LeftToRightListNumberIcon,
  Link01Icon,
  Redo02Icon,
  TextBoldIcon,
  TextItalicIcon,
  Undo02Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { type Editor, useEditorState } from "@tiptap/react";
import type { ComponentProps } from "react";

import { Button } from "@/shared/ui/button";

type ToolbarButtonProps = {
  label: string;
  icon: ComponentProps<typeof HugeiconsIcon>["icon"];
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
};

function ToolbarButton({
  label,
  icon,
  onClick,
  active,
  disabled,
}: ToolbarButtonProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      aria-label={label}
      title={label}
      // A toggle button: the state is read out by screen readers, not shown by color alone
      aria-pressed={active}
      disabled={disabled}
      className="aria-pressed:bg-muted aria-pressed:text-foreground"
      // Keep the selection in the document while the mouse clicks the toolbar
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      <HugeiconsIcon icon={icon} aria-hidden strokeWidth={2} />
    </Button>
  );
}

function Divider() {
  return <span aria-hidden="true" className="mx-1 h-6 w-px bg-border" />;
}

type RichTextToolbarProps = {
  editor: Editor;
  onLink: () => void;
};

/** Only the formatting the schema allows (extensions.ts): headings, bold, italic, lists, link. */
export function RichTextToolbar({ editor, onLink }: RichTextToolbarProps) {
  // Re-render only when one of these flags changes, not on every keystroke
  const state = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      h2: e.isActive("heading", { level: 2 }),
      h3: e.isActive("heading", { level: 3 }),
      bold: e.isActive("bold"),
      italic: e.isActive("italic"),
      bulletList: e.isActive("bulletList"),
      orderedList: e.isActive("orderedList"),
      link: e.isActive("link"),
      canUndo: e.can().undo(),
      canRedo: e.can().redo(),
    }),
  });
  const chain = () => editor.chain().focus();

  return (
    <div
      role="toolbar"
      aria-label="Formatowanie tekstu"
      className="flex flex-wrap items-center gap-0.5 border-b p-1"
    >
      <ToolbarButton
        label="Nagłówek"
        icon={Heading02Icon}
        active={state.h2}
        onClick={() => chain().toggleHeading({ level: 2 }).run()}
      />
      <ToolbarButton
        label="Podtytuł"
        icon={Heading03Icon}
        active={state.h3}
        onClick={() => chain().toggleHeading({ level: 3 }).run()}
      />
      <Divider />
      <ToolbarButton
        label="Pogrubienie"
        icon={TextBoldIcon}
        active={state.bold}
        onClick={() => chain().toggleBold().run()}
      />
      <ToolbarButton
        label="Kursywa"
        icon={TextItalicIcon}
        active={state.italic}
        onClick={() => chain().toggleItalic().run()}
      />
      <Divider />
      <ToolbarButton
        label="Lista"
        icon={LeftToRightListBulletIcon}
        active={state.bulletList}
        onClick={() => chain().toggleBulletList().run()}
      />
      <ToolbarButton
        label="Lista numerowana"
        icon={LeftToRightListNumberIcon}
        active={state.orderedList}
        onClick={() => chain().toggleOrderedList().run()}
      />
      <Divider />
      <ToolbarButton
        label="Link"
        icon={Link01Icon}
        active={state.link}
        onClick={onLink}
      />
      <Divider />
      <ToolbarButton
        label="Cofnij"
        icon={Undo02Icon}
        disabled={!state.canUndo}
        onClick={() => chain().undo().run()}
      />
      <ToolbarButton
        label="Ponów"
        icon={Redo02Icon}
        disabled={!state.canRedo}
        onClick={() => chain().redo().run()}
      />
    </div>
  );
}
