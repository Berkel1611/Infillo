/** A safe in-app path from ?next=, or "/" (never an external address). */
export function safeNextPath(next: string | null | undefined): string {
  if (
    !next ||
    !next.startsWith("/") ||
    next.startsWith("//") || // protocol-relative URL: //evil.example
    next.startsWith("/\\") || // some browsers treat "/\" like "//"
    next.startsWith("/login") ||
    next.startsWith("/register") // would loop back to the form
  ) {
    return "/";
  }
  return next;
}

/** path, with ?next= appended unless it is the default "/". */
export function withNext(path: string, next: string): string {
  return next === "/" ? path : `${path}?next=${encodeURIComponent(next)}`;
}
