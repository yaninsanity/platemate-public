<div align="center">
  <img src="frontend/assets/logo4.png" alt="PlateMate" width="200" height="auto" />
</div>

# PlateMate

[![DOI](https://img.shields.io/badge/DOI-10.1145%2F3764687.3769926-B31B1B)](https://doi.org/10.1145/3764687.3769926)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB)](.python-version)

Research artifact for the OZCHI '25 paper **"PlateMate: Structured Guidance
Design in Relatedness Technology for Remote Joint Activity"**
([10.1145/3764687.3769926](https://doi.org/10.1145/3764687.3769926)).

The paper studies how *structured guidance* — recipes as a shared script,
weekly rounds as a shared rhythm, an AI judge as a shared referee — supports
relatedness between partners who cannot cook in the same kitchen. This
repository is the system that study ran on, released so the design can be
inspected, reproduced and built on.

Concretely: partners cook the same recipe apart, photograph the result, an AI
judge scores each dish across three dimensions, and the outcome feeds a shared
album, a weekly battle history and a virtual pet raised jointly. Django REST
backend, Vue 3 frontend.

> The code is released as it ran, not as a polished library. Comments and
> naming reflect a research prototype under time pressure; the licensing,
> provenance and configuration have been cleaned up for release, the
> architecture has not been rewritten for it.

## What is in it

| Area | What it does |
|---|---|
| `recipes` | Recipes, ingredients, menus, cooking diary entries |
| `cookai` | OpenAI-backed judging: scoring, two-dish comparison, ingredient detection from a photo |
| `couplememory` | The shared album, memory posts and weekly rounds between two people |
| `petcare` | The virtual pet: hunger, missions, rewards, reminders, badges |
| `users` | Custom user model, couples, avatars, token auth |
| `sms_service` | Verification codes over a self-hosted Textbelt instance |
| `analytics` | Event tracking and the admin dashboard built on it |
| `system` | Runtime configuration editable from the admin |

The frontend covers login and registration, couple setup, the home arena,
round quests and battles, battle history, the memory album, family menus, a
market-find view, badges, messages and profiles.

## Requirements

- **Python 3.13.** Not 3.14 — the pinned `pydantic-core` has no wheel for it
  and the Rust fallback build fails. `.python-version` and the Docker image
  both pin 3.13.
- **Node 18+ with Yarn** for the frontend.
- **Docker** only if you want the container path.
- An **OpenAI API key** if you want the judging features. Without one the app
  still runs; CookAI falls back to stub mode.

## Quick start

### 1. Clone

```bash
git clone https://github.com/yaninsanity/platemate-public.git
cd platemate-public
```

### 2. Configure

Credentials are never committed. Each machine creates its own.

```bash
git config core.hooksPath .githooks     # refuses commits containing secrets
cp backend/.env.example backend/.env    # then fill it in
./scripts/gen-dev-certs.sh              # local self-signed certificates
```

`DJANGO_SECRET_KEY` is required and the app will not start without it:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Leave `DJANGO_ENV=dev` to use SQLite. Set it to `prod` to switch to
PostgreSQL, which then also needs the `POSTGRES_*` values.

### 3. Backend

Note the paths: `manage.py` lives in `backend/app`, while `requirements.txt`
lives one level up in `backend`.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend/app
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:911
```

- API: <http://localhost:911/api/>
- Admin: <http://localhost:911/admin/>
- Health: <http://localhost:911/api/health/>
- CookAI test console: <http://localhost:911/admin/cookai/openai-test/>

### 4. Frontend

Outside Docker you must point the dev proxy at your local backend. Its default
target is `http://web-dev:911`, which is a compose service name and only
resolves inside Docker.

```bash
cd frontend
yarn install
VITE_API_BASE_URL=http://localhost:911/api yarn dev
```

Vite serves on <http://localhost:520> — the port is set in `vite.config.ts`
and overridable with `VITE_DEV_PORT`. It proxies `/api`, `/media` and `/admin`
through to Django, so run the backend first. `yarn build` produces a
production bundle and `yarn preview` serves it.

## Docker

Every service sits behind a compose profile, so a bare `docker compose up`
starts nothing. Choose one:

```bash
docker compose --profile dev up --build          # web-dev + frontend-dev
docker compose --profile prod up --build         # web + frontend + https-prod
docker compose --profile https up --build        # nginx TLS front only
```

| Service | Profile |
|---|---|
| `web`, `frontend`, `https-prod` | `prod` |
| `web-dev`, `frontend-dev` | `dev` |
| `https-dev` | `https` |

On Apple Silicon or another ARM host:

```bash
export DOCKER_PLATFORM=linux/arm64/v8
```

## Entity relationship diagram

![PlateMate ERD](backend/erd.png)

Generated from the Django models. Regenerate it after a schema change:

```bash
docker compose run --rm web \
  sh -c "python manage.py graph_models -a --group-models -o /usr/src/app/erd.dot && \
         dot -Tpng /usr/src/app/erd.dot -o /usr/src/app/erd.png"
```

## SMS verification

Verification codes go through a self-hosted [Textbelt](https://textbelt.com)
container. Export your own SMTP credentials first — never inline them into the
command.

```bash
docker pull hexeth/textbelt-docker
docker run -d --name textbelt -p 110:9090 \
  -e HOST="smtp.office365.com" -e MAIL_PORT="587" \
  -e MAIL_USER="$SMTP_USER" -e MAIL_PASS="$SMTP_PASSWORD" \
  -e FROM_ADDRESS="$SMTP_FROM" -e REALNAME="$SMTP_REALNAME" \
  --restart unless-stopped hexeth/textbelt-docker
```

## Layout

```
backend/
  requirements.txt
  .env.example          configuration template, no real values
  app/                  Django project root; manage.py lives here
frontend/
  src/                  Vue 3 application
  public/biped/         3D character model and animations
scripts/
  gen-dev-certs.sh      local self-signed certificates
.githooks/
  pre-commit            refuses credential files and key-shaped strings
```

## Contributing

`CONTRIBUTING.md` has the short version: open an issue first for anything
beyond a small fix, enable the secret-guard hook, keep comments in English.
`CODE_OF_CONDUCT.md` applies to every project space. Security problems go
through `SECURITY.md`, never a public issue.

## Citing this work

If you use PlateMate in academic work, cite the paper rather than the
repository. GitHub also renders **Cite this repository** from `CITATION.cff`.

```bibtex
@inproceedings{wang2025platemate,
  author    = {Wang, Wei-Lu and Yan, Zeren and Zheng, Xian and
               Zhang, Wuyou and Cao, Yufei and McCrickard, D. Scott},
  title     = {{PlateMate}: Structured Guidance Design in Relatedness
               Technology for Remote Joint Activity},
  booktitle = {Proceedings of the 37th Australian Conference on
               Human-Computer Interaction},
  series    = {OZCHI '25},
  year      = {2025},
  pages     = {755--762},
  publisher = {Association for Computing Machinery},
  doi       = {10.1145/3764687.3769926}
}
```

## Licensing

Code is MIT licensed; see `LICENSE`. Authors and contributors are listed in
`AUTHORS`, which maps each paper author to their GitHub account; copyright is
held jointly.

`NOTICE` covers everything `LICENSE` does not: the pet egg model is
third-party under CC BY 4.0 and keeps its own terms, the raster art is
AI-generated with its C2PA provenance intact, and the dependency licensing
position is recorded there. Read it before redistributing.

## About the name

The naming rationale below is the design argument the paper builds on: the
metaphor is not branding but a statement of what the system is for.

PlateMate grew out of two very ordinary Australian ideas: you "plate up" when
food's ready, and you look after your "mate" when it matters. Leveraging HCI
work on shared artifacts, we treat the plate as a tangible interface where
memories and routines are made visible. As every backyard barbie shows, people
rarely remember the ingredient list — they remember who stood next to them at
the grill — so taste is co-created, not consumed. The "mate" half encodes
practical care over poetic promises, mirroring Australian mateship's low-fuss,
do-something ethos rather than pushy notifications. Embedding this in a roundly
cook quest reframes "relationship maintenance" as a playful ritual instead of a
chore. Mobile, asynchronous play turns a shared plate into a timezone-neutral
surface for coordination, reflection and reward. Accordingly, the name isn't
cute branding; it's our design spec: Plate = the memory canvas, Mate = the
maintenance contract. Together they signal a system that presents feelings and
binds routines without feeling like homework. End to end, "PlateMate" states
our thesis in two syllables and a wink to an OzCHI audience: food is the
interface, mateship is the interaction model.
