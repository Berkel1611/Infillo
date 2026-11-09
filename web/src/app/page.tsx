import { BackendStatus } from "@/features/health/components/BackendStatus";

export default function HomePage() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-4 px-4 py-12">
      <h1 className="text-3xl font-semibold">Infillo</h1>
      <BackendStatus />
    </main>
  );
}
