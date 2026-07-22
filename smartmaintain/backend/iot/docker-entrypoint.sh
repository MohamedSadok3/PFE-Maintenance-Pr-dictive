#!/bin/sh
set -e
pip install -q psycopg2-binary 2>/dev/null || true
exec "$@"
