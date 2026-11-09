import { BackendStatus } from "@/features/health/components/BackendStatus";
import { PalettePreview } from "@/features/theme-preview/components/PalettePreview";

export default function HomePage() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-8 px-4 py-12">
      <div className="flex flex-col gap-4">
        <h1 className="text-3xl font-semibold">Infillo</h1>
        <BackendStatus />
      </div>
      <PalettePreview />
    </main>
  );
}
