# Contributing

Thanks for taking an interest.

This repository is a research artifact accompanying an OZCHI '25 paper, not a
product under active feature development. That shapes what is likely to be
merged: fixes, portability improvements, clearer documentation and tests are
welcome; large redesigns are better discussed in an issue first, because the
code needs to stay recognisable as the system the paper describes.

## Before you start

Open an issue first for anything beyond a small fix. It saves you writing code
that turns out to duplicate work in progress or point away from where the
project is going.

## Setting up

`README.md` has the full path from clone to running app. Two things trip people
up, so they are worth repeating:

- Use **Python 3.13**. 3.14 has no wheel for the pinned `pydantic-core` and the
  fallback build fails.
- Outside Docker, start the frontend as
  `VITE_API_BASE_URL=http://localhost:911/api yarn dev`. Its default proxy
  target is a compose service name that only resolves inside Docker.

Enable the secret-guard hook on your first clone:

```bash
git config core.hooksPath .githooks
```

It refuses commits that add `.env`, `*.pem`, `*.key` or `*.sqlite3`, and
rejects staged content matching common API-key shapes. If it stops you, put the
value in `backend/.env` instead. If it stops you wrongly, `--no-verify` exists,
but be sure.

## Pull requests

- One change per pull request.
- Say what breaks if the change is wrong. That is the part reviewers cannot
  reconstruct themselves.
- Run `python manage.py check` from `backend/app` and `yarn build` from
  `frontend` before pushing.
- Comments and identifiers in English.

## Reporting a security issue

Do not open a public issue. See `SECURITY.md`.

## Licensing of contributions

Contributions are accepted under the MIT License in `LICENSE`. By opening a
pull request you agree your contribution may be distributed under it, and you
are added to `AUTHORS`.
