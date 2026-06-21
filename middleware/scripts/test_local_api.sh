#!/usr/bin/env bash
# Corre después de `sam local start-api` (puerto 3000 por defecto), o
# después de `sam deploy` (cambia BASE_URL y agrega -H "x-api-key: ...").
set -e
BASE_URL="${BASE_URL:-http://127.0.0.1:3000}"

echo "== verify carrier =="
curl -s -X POST "$BASE_URL/carrier/verify" \
  -H "Content-Type: application/json" \
  -d '{"mc_number": "872144"}'
echo

echo "== search loads =="
curl -s -X POST "$BASE_URL/loads/search" \
  -H "Content-Type: application/json" \
  -d '{"origin_state": "GA", "destination_state": "TX", "equipment_type": "DRY_VAN", "max_results": 5}'
echo

echo "== get load =="
curl -s "$BASE_URL/loads/LD0000045821"
echo

echo "== book load =="
curl -s -X POST "$BASE_URL/loads/LD0000045821/book" \
  -H "Content-Type: application/json" \
  -d '{"mc_number": "872144", "agreed_rate": 2200}'
echo

echo "== negotiate =="
curl -s -X POST "$BASE_URL/negotiate" \
  -H "Content-Type: application/json" \
  -d '{"load_id": "LD0000045821", "carrier_offer": 2300, "round": 1}'
echo

