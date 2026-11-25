import { Badge } from "@/shared/ui/badge";

import { availabilityLabels } from "../availability";
import type { Availability } from "../types";

const variants = {
  AVAILABLE: "secondary",
  MADE_TO_ORDER: "outline",
  OUT_OF_STOCK: "destructive",
} as const;

/** The status is always spelled out in words: color only reinforces it. */
export function AvailabilityBadge({
  availability,
}: {
  availability: Availability;
}) {
  return (
    <Badge variant={variants[availability]}>
      {availabilityLabels[availability]}
    </Badge>
  );
}
