#!/bin/bash
# Reset the working copy (data/campus_customs_new.db) to the original values.
# The original data/campus_customs.db is never modified. This wipes every account,
# chat message, and stock change made through the site since the last reset.
cd "$(dirname "$0")"
cp data/campus_customs.db data/campus_customs_new.db
chmod 600 data/campus_customs_new.db   # the original is read-only; the copy must be writable
rm -f data/campus_customs_new.db-journal
echo "Working copy data/campus_customs_new.db reset to original values."
