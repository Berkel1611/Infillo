import { ApiError } from "./client";

// Error of the whole request: the "code" field of the API response
const messages: Record<string, string> = {
  INVALID_CREDENTIALS: "Nieprawidłowy login lub hasło.",
  EMAIL_TAKEN:
    "Konto z tym adresem e-mail już istnieje. Zaloguj się albo użyj innego adresu.",
  USERNAME_TAKEN: "Ta nazwa użytkownika jest już zajęta. Wybierz inną.",
  NOT_AUTHENTICATED: "Sesja wygasła. Zaloguj się ponownie.",
  FORBIDDEN: "Nie masz uprawnień do tej operacji.",
  NOT_FOUND: "Nie znaleziono strony lub danych.",
  USER_NOT_FOUND: "Nie znaleziono użytkownika.",
  CANNOT_MODIFY_SELF: "Nie możesz zmienić własnego konta w tym miejscu.",
  CANNOT_MODIFY_ADMIN: "Nie można zmieniać kont administratorów.",
  CATEGORY_NOT_FOUND: "Nie znaleziono takiej kategorii.",
  CATEGORY_NAME_TAKEN:
    "Kategoria o tej nazwie już istnieje w tym miejscu. Wybierz inną nazwę.",
  CATEGORY_TOO_DEEP: "Kategorie mogą mieć najwyżej trzy poziomy.",
  CATEGORY_CYCLE:
    "Nie można przenieść kategorii do niej samej ani do jej podkategorii.",
  CATEGORY_NOT_EMPTY:
    "Nie można usunąć kategorii, która ma podkategorie lub produkty.",
  CATEGORY_NOT_MANAGED: "Nie zarządzasz tą kategorią.",
  USER_NOT_MODERATOR: "Do kategorii można przydzielić tylko moderatorów.",
  PRODUCT_NOT_FOUND: "Nie znaleziono takiego produktu.",
  VARIANT_NOT_FOUND: "Nie znaleziono wariantu tego produktu.",
  DUPLICATE_VARIANT:
    "Warianty nie mogą się powtarzać: kolor, materiał i rozmiar muszą się różnić.",
  PUBLISH_REQUIRES_VARIANT:
    "Aby opublikować produkt, dodaj co najmniej jeden wariant.",
  PUBLISH_REQUIRES_DESCRIPTION: "Aby opublikować produkt, uzupełnij jego opis.",
  VALIDATION_ERROR: "Sprawdź dane w formularzu.",
  TOO_MANY_REQUESTS: "Zbyt wiele prób. Spróbuj ponownie za chwilę.",
  INTERNAL_ERROR: "Wystąpił błąd serwera. Spróbuj ponownie za chwilę.",
  NETWORK_ERROR:
    "Brak połączenia z serwerem. Sprawdź internet i spróbuj ponownie.",
};

// Error of one form field: the "type" of an item in "fields" (DRF and Django validator codes)
const fieldMessages: Record<string, string> = {
  required: "To pole jest wymagane.",
  blank: "To pole jest wymagane.",
  min_length: "Wartość jest za krótka.",
  max_length: "Wartość jest za długa.",
  invalid: "Wartość jest nieprawidłowa.",
  invalid_choice: "Wybierz jedną z dostępnych opcji.",
  null: "To pole jest wymagane.",
  min_value: "Wartość jest za mała.",
  max_value: "Wartość jest za duża.",
  max_digits: "Wartość ma za dużo cyfr.",
  max_decimal_places: "Podaj najwyżej dwa miejsca po przecinku.",
  max_whole_digits: "Wartość jest za duża.",
  does_not_exist: "Wybrana pozycja nie istnieje.",
  duplicate_variant:
    "Warianty nie mogą się powtarzać: kolor, materiał i rozmiar muszą się różnić.",
  // Product description: codes of the server-side allowlist (api/apps/catalog/rich_text.py)
  invalid_document: "Opis ma nieprawidłowy format.",
  node_not_allowed: "Opis zawiera element, który nie jest dozwolony.",
  mark_not_allowed: "Opis zawiera formatowanie, które nie jest dozwolone.",
  attr_not_allowed: "Opis zawiera niedozwoloną właściwość.",
  link_not_allowed:
    "Opis zawiera niedozwolony link. Dozwolone są tylko adresy http i https.",
  document_too_large: "Opis jest zbyt długi lub zbyt zagnieżdżony.",
  invalid_username:
    "Nazwa użytkownika może zawierać tylko litery, cyfry oraz znaki . + - _",
  invalid_postal_code: "Podaj kod pocztowy w formacie 00-000.",
  invalid_phone: "Telefon może zawierać tylko cyfry, spacje i znak +.",
  password_too_short: "Hasło musi mieć co najmniej 8 znaków.",
  password_too_common: "To hasło jest zbyt popularne. Wybierz inne.",
  password_entirely_numeric: "Hasło nie może składać się z samych cyfr.",
  password_too_similar: "Hasło jest zbyt podobne do Twoich danych.",
};

const FALLBACK = "Ups! Coś poszło nie tak. Spróbuj ponownie za chwilę.";
const FIELD_FALLBACK = "Sprawdź to pole.";

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return messages[error.code] ?? FALLBACK;
  }
  return FALLBACK;
}

export function fieldErrorMessage(type: string): string {
  return fieldMessages[type] ?? FIELD_FALLBACK;
}
