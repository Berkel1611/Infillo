import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-start gap-4 px-4 py-16">
      <p className="text-sm font-medium text-muted-foreground">Błąd 404</p>
      <h1 className="text-3xl font-semibold">Nie znaleźliśmy tej strony</h1>
      <p className="text-muted-foreground">
        Adres może być błędny albo strona została usunięta.
      </p>
      <Link
        href="/"
        className="rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground hover:opacity-90"
      >
        Wróć na stronę główną
      </Link>
    </div>
  );
}
