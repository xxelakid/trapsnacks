# TrapSnacks: Deploy to Render with a Neon database

The live app runs on **Render** (web service) and stores its data in **Neon** (PostgreSQL).
Render redeploys automatically every time something is merged into the `main` branch on GitHub.

## Render web service settings

| Setting | Value |
|---|---|
| Source | This GitHub repository, branch `main` |
| Runtime | Python |
| Root Directory | (blank) |
| Build command | `pip install -r requirements.txt` |
| Start command | `python init_db.py && gunicorn --worker-class gthread --workers 1 --threads 20 --bind 0.0.0.0:$PORT app:app` |

## Environment variables (Render > your service > Environment)

| Name | What it is |
|---|---|
| `DATABASE_URL` | The Neon connection string (Neon > Dashboard > Connect). Keep it secret. |
| `SECRET_KEY` | A random secret of at least 32 characters. |
| `ADMIN_USERNAME` | The first owner account's username (only used if no owner exists yet). |
| `ADMIN_PASSWORD` | That owner's password, at least 12 characters. |
| `DEMO_MENU` | Optional. `1` adds the demo menu to an EMPTY database. |
| `PYTHON_VERSION` | Optional. The Python version Render should use. |

`config.py` reads `DATABASE_URL` and converts `postgres://` / `postgresql://` into the
`postgresql+psycopg://` form SQLAlchemy needs. Without `DATABASE_URL` (on your own laptop)
the app uses the local SQLite file `instance/trapsnacks.db`.

## What happens on every deploy

1. `pip install -r requirements.txt` installs the packages (including `gunicorn` and `psycopg`).
2. `python init_db.py`:
   - creates any missing tables (from `models.py`);
   - **upgrades** existing tables safely (for example adds the `user.active` column) without deleting data;
   - creates the first owner account if there is none;
   - adds the demo menu if `DEMO_MENU=1` and the menu is empty.
3. `gunicorn ... app:app` starts the web server. One worker is used because the live-update
   rooms (Flask-SocketIO) live in one process; 20 threads let many devices connect at once.

## Important

- **Never run `python seed.py` against Neon.** It deletes every table. It is only for your own laptop.
- Never commit `DATABASE_URL`, passwords or `SECRET_KEY` to GitHub. They live only in Render.
- The free Render instance sleeps after inactivity; the first visit after that is slow and
  screens reconnect automatically.
