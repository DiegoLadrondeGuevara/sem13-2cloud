#!/usr/bin/env bash
set -euo pipefail

expected_account=904208419583
actual_account="$(aws sts get-caller-identity --query Account --output text)"
actual_arn="$(aws sts get-caller-identity --query Arn --output text)"
printf 'Cuenta AWS: %s\nIdentidad: %s\n' "$actual_account" "$actual_arn"

if [[ "$actual_account" != "$expected_account" ]]; then
  printf 'ERROR: la cuenta debe ser %s. No se desplegara nada.\n' "$expected_account" >&2
  exit 1
fi
if [[ "$actual_arn" != arn:aws:sts::904208419583:assumed-role/LabRole/* ]]; then
  printf 'ERROR: la instancia EC2 debe usar LabRole. No se desplegara nada.\n' >&2
  exit 1
fi
