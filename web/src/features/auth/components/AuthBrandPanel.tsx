const POINTS = [
  "Gotowe wydruki w wybranym kolorze i materiale",
  "Zdjęcia wydruków i komentarze społeczności",
  "Prośba o wydruk na zamówienie, prosto do opiekuna kategorii",
];

/** Decorative side panel of the login and registration pages (desktop only). */
export function AuthBrandPanel() {
  return (
    <div className="relative hidden overflow-hidden rounded-3xl bg-primary p-10 text-primary-foreground lg:order-first lg:flex lg:min-h-[34rem] lg:flex-col lg:justify-end">
      {/* Rotated grid: like the infill of a 3D print */}
      <svg
        aria-hidden
        className="absolute inset-0 size-full text-primary-foreground/15"
      >
        <defs>
          <pattern
            id="infill"
            width="48"
            height="48"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <path
              d="M0 0H48M0 0V48"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#infill)" />
      </svg>

      <div className="relative flex flex-col gap-6">
        <p className="text-5xl font-semibold tracking-tight">Infillo</p>
        <p className="text-xl text-primary-foreground/90">
          Wydruki 3D od ludzi, którzy sami drukują.
        </p>
        <ul className="flex flex-col gap-3 text-primary-foreground/80">
          {POINTS.map((point) => (
            <li key={point} className="flex gap-3">
              <span
                aria-hidden
                className="mt-2 size-2 shrink-0 rounded-full bg-primary-foreground"
              />
              {point}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
