#!/bin/bash
set -e

cd /app/node_modules/@secvisogram/csaf-validator-service || exit 1

# Run dev server
npm run dev
