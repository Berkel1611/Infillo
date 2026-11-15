"use client";

import { AlertCircleIcon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { type ReactNode, useEffect, useRef } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";

type FormAlertProps = {
  title: string;
  children: ReactNode;
  /** Move keyboard focus to the alert when it appears. */
  focusOnShow?: boolean;
};

export function FormAlert({
  title,
  children,
  focusOnShow = true,
}: FormAlertProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (focusOnShow) {
      ref.current?.focus();
    }
  }, [focusOnShow]);

  return (
    <Alert
      ref={ref}
      tabIndex={-1} // focusable by script only, not a Tab stop
      variant="destructive"
      className="outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <HugeiconsIcon icon={AlertCircleIcon} aria-hidden />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  );
}
