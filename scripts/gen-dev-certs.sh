#!/usr/bin/env bash
# Generate a self-signed certificate for local development into certs/.
# certs/ is gitignored — these files are never committed.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p certs
HOST="${1:-localhost}"
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout certs/key.pem -out certs/cert.pem \
  -subj "/CN=${HOST}" \
  -addext "subjectAltName=DNS:${HOST},DNS:localhost,IP:127.0.0.1"
chmod 600 certs/key.pem
echo "Generated certs/cert.pem and certs/key.pem (CN=${HOST}, valid 365 days)"
