import { Button } from "@/shared/ui/button";

const SWATCHES = [
  { label: "Główny", className: "bg-primary text-primary-foreground" },
  { label: "Drugi", className: "bg-secondary text-secondary-foreground" },
  { label: "Akcent", className: "bg-brand-accent text-foreground" },
  { label: "Tło wyciszone", className: "bg-muted text-muted-foreground" },
  { label: "Karta", className: "bg-card text-card-foreground border" },
];

export function PalettePreview() {
  return (
    <section aria-labelledby="palette-heading" className="flex flex-col gap-4">
      <h2 id="palette-heading" className="text-xl font-semibold">
        Paleta kolorów
      </h2>
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {SWATCHES.map((swatch) => (
          <li
            key={swatch.label}
            className={`rounded-lg p-4 text-sm font-medium ${swatch.className}`}
          >
            {swatch.label}
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-3">
        <Button>Przycisk główny</Button>
        <Button variant="secondary">Przycisk drugi</Button>
        <Button variant="outline">Obramowany</Button>
      </div>
    </section>
  );
}
