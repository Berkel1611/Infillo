# Infillo

Sklep internetowy z wydrukami 3D połączony ze społecznością. Projekt zaliczeniowy z przedmiotu *Projektowanie aplikacji internetowych* (2026/27).

## Technologie

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui (Base UI)
- **Infrastruktura:** Docker Compose (PostgreSQL, Mailpit)

## Wymagania

- Docker Desktop
- Python 3.12+
- Node.js 20+

## Uruchomienie

### 1. Baza danych i poczta testowa

```bash
cp .env.example .env
docker compose up -d
```

Jeśli Windows zgłosi, że port 1025 jest niedostępny (zarezerwowany przez system), ustaw w `.env` inny, np. `MAILPIT_SMTP_PORT=2525`.

### 2. Backend (`api/`)

```bash
cd api
python -m venv venv
venv\Scripts\activate        # Linux / macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API: http://localhost:8000, dokumentacja: http://localhost:8000/docs

### 3. Frontend (`web/`)

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

Aplikacja: http://localhost:3000

## Adresy

| Usługa | Adres |
|---|---|
| Aplikacja | http://localhost:3000 |
| API | http://localhost:8000 |
| Podgląd wysłanych e-maili (Mailpit) | http://localhost:8025 |
| PostgreSQL | localhost:5432 |

## Testy i jakość kodu

```bash
# backend (w api/, z aktywnym venv; testy tworzą i usuwają bazę infillo_test)
pytest
ruff check .
ruff format --check .

# frontend (w web/)
npm run lint
npm run format:check
npm run build
```

## Kolorystyka

Trzy kolory bazowe aplikacji są w pliku `web/public/theme.css`. Pozostałe kolory są z nich wyliczane (`web/src/app/globals.css`), więc zmiana tych trzech wartości zmienia tonację całej aplikacji. Zmiana działa po odświeżeniu strony, bez przebudowy.