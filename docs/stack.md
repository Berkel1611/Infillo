# Stack technologiczny – sklep z wydrukami 3D

Projekt: *Projektowanie aplikacji internetowych 2026/27* (dr Karol Pąk)
Tryb pracy: samodzielnie, oddawanie etapami, cel: wszystkie bonusy.

---

## Architektura w skrócie

```
            przeglądarka
                 │
        reverse proxy (jedna domena)
           │                 │
     /  → web (Next.js)   /api → api (ASP.NET Core)
                                   │
                         db (PostgreSQL)   pliki (wolumen)
                                   │
                         mailpit (dev) / SMTP (prod)
```

- **Next.js = czysty frontend.** Cała logika biznesowa jest w API .NET, a Next nie ma własnej bazy ani logiki w API routes / server actions.
- Przy renderowaniu po stronie serwera Next przekazuje do API ciasteczko z tokenem.
- Oba serwisy działają pod wspólną domeną (`/` i `/api`), dzięki czemu ciasteczka HttpOnly działają bez problemów z CORS.

---

## Frontend

| Obszar | Technologia | Uwagi |
|---|---|---|
| Framework | **Next.js (App Router) + TypeScript** | SSR stron produktów → SEO pod przyszłe wdrożenie |
| Stylowanie | CSS Modules lub Tailwind v4 z własnymi tokenami | brak gotowych, niezmodyfikowanych komponentów |
| Kolorystyka | 3 zmienne CSS: `--primary`, `--secondary`, `--accent` | reszta palety liczona przez `color-mix()` / `oklch()`; podstawa pod motywy |
| Dostępność | **Radix UI Primitives** (headless) | gotowa obsługa klawiatury, fokusu, Esc; wygląd w całości własny |
| Dane z API | **TanStack Query** | cache, odświeżanie, stany ładowania |
| Formularze | **React Hook Form + Zod** | walidacja, zachowanie wartości pól po błędzie |
| Edytor HTML | **Tiptap** | opisy postów/produktów |
| Drag & drop | **dnd-kit** | obsługuje też klawiaturę |
| Slider | **własna implementacja** | zapętlony, 1/2/3 karty zależnie od szerokości, przesuw o 1, karty wyrównane do najwyższej |

---

## Backend

| Obszar | Technologia | Uwagi |
|---|---|---|
| Framework | **ASP.NET Core Web API (.NET 10 LTS), C#** | Minimal APIs lub kontrolery |
| ORM | **EF Core + Npgsql** | migracje; zapytania parametryzowane → odporność na SQL injection |
| Uwierzytelnianie | **ASP.NET Core Identity + JWT** | access token + refresh token w ciasteczku HttpOnly (ocena 4.0) |
| Social login | **Facebook, Microsoft** (wbudowane) + **Discord** (`AspNet.Security.OAuth.Providers`) | ≥ 2 portale spoza Google/GitHub; profil uzupełniany danymi z portalu |
| Walidacja | **FluentValidation** | |
| Sanityzacja HTML | **HtmlSanitizer** | ochrona przed XSS w treściach z edytora |
| Skalowanie zdjęć | **SkiaSharp** lub **ImageSharp** | lokalnie, przy uploadzie; licencję ImageSharp sprawdzić przed wdrożeniem komercyjnym |
| E-mail | **MailKit** | potwierdzenie zamówienia i oczekiwania na płatność |
| Płatności | **Stripe (test mode)** lub **PayU sandbox** | webhook automatycznie zmienia status zamówienia |
| Dokumentacja API | **OpenAPI + Scalar / Swagger UI** | |

---

## Dane i pliki

- **PostgreSQL** – główna baza.
- **Zdjęcia** – lokalny wolumen Dockera, z możliwością późniejszej migracji na S3.
- **Seed** – przykładowe kategorie, produkty, posty oraz konta dla każdej roli (administrator, moderator, użytkownik).

---

## Infrastruktura i uruchomienie

**Docker Compose**, cztery serwisy:

| Serwis | Rola |
|---|---|
| `web` | Next.js |
| `api` | ASP.NET Core |
| `db` | PostgreSQL |
| `mailpit` | lokalna skrzynka do podglądu wysyłanych maili |

- Uruchomienie całości: `docker compose up`.
- Konfiguracja przez plik `.env`, z dołączonym `.env.example` bez sekretów.
- To spełnia wymóg dostarczenia konfiguracji umożliwiającej uruchomienie projektu.

---

## Testy

| Warstwa | Narzędzia |
|---|---|
| Backend | **xUnit + Testcontainers** (testy integracyjne na prawdziwym PostgreSQL) |
| Frontend / E2E | **Playwright** |
| Dostępność | **axe-core** (w Playwright) + ręczne testy klawiaturą |

---

## Do pamiętania

- Podstrona celowo łamiąca WCAG ma być odizolowana (osobna ścieżka / flaga) i wyłączona przy wdrożeniu produkcyjnym.
- Klucze OAuth i płatności trzymaj tylko w `.env`, nigdy w repozytorium.
