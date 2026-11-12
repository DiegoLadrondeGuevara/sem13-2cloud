#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/check-aws.sh
npm ci
npx serverless --version
npx serverless package --stage dev --region us-east-1
python3 - <<'PY'
import json

with open('.serverless/cloudformation-template-update-stack.json', encoding='utf-8') as stream:
    template = json.load(stream)
bucket = template['Outputs']['BucketName']['Value']
expected = 'sem13-2cloud-dev-904208419583'
print(f'Bucket del paquete Serverless: {bucket}')
if bucket != expected:
    raise SystemExit(f'ERROR: el paquete no corresponde a la cuenta 904208419583. Despliegue cancelado.')
roles = [name for name, resource in template['Resources'].items() if resource['Type'] == 'AWS::IAM::Role']
if roles:
    raise SystemExit(f'ERROR: el paquete intenta crear roles IAM: {roles}. Despliegue cancelado.')
PY
npx serverless deploy --package .serverless --stage dev --region us-east-1 --verbose
