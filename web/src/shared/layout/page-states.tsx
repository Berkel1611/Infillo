import { HugeiconsIcon } from "@hugeicons/react";
import type { ComponentProps, ReactNode } from "react";

import { Spinner } from "@/shared/ui/spinner";

export function PageSpinner() {
  return (
    <div className="flex justify-center py-16">
      <Spinner className="size-6" />
    </div>
  );
}

type PageMessageProps = {
  icon: ComponentProps<typeof HugeiconsIcon>["icon"];
  title: string;
  description: string;
  action?: ReactNode;
  heading?: "h1" | "h2";
};

/** A centered message: no access, no connection... */
export function PageMessage({
  icon,
  title,
  description,
  action,
  heading: Heading = "h1",
}: PageMessageProps) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 px-4 py-16 text-center">
      <HugeiconsIcon
        icon={icon}
        aria-hidden
        className="size-10 text-muted-foreground"
      />
      <Heading className="text-2xl font-semibold">{title}</Heading>
      <p className="text-muted-foreground">{description}</p>
      {action}
    </div>
  );
}
