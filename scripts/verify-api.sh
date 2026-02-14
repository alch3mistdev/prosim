#!/usr/bin/env bash
# Verify ProSim API is working. Run with backend already started on port 8000.
# Usage: ./scripts/verify-api.sh

set -e
BASE="${1:-http://127.0.0.1:8000}"

echo "Testing ProSim API at $BASE"
echo ""

# Test history endpoint
echo "1. GET /api/history"
curl -s "$BASE/api/history?limit=5" | head -c 200
echo ""
echo ""

# Test workflow parse (no Claude needed)
echo "2. POST /api/workflow/parse (valid JSON)"
curl -s -X POST "$BASE/api/workflow/parse" \
  -H "Content-Type: application/json" \
  -d '{"data":{"name":"Test","nodes":[{"id":"start","name":"Start","node_type":"start","params":{}},{"id":"end","name":"End","node_type":"end","params":{}}],"edges":[{"source":"start","target":"end"}]}}' \
  | head -c 300
echo ""
echo ""

# Test workflow generate (requires ANTHROPIC_API_KEY)
echo "3. POST /api/workflow/generate (requires ANTHROPIC_API_KEY)"
if curl -s -X POST "$BASE/api/workflow/generate" \
  -H "Content-Type: application/json" \
  -d '{"description":"simple two-step process"}' \
  --max-time 30 \
  -w "\nHTTP Status: %{http_code}\n" -o /tmp/prosim-gen.json; then
  status=$(tail -1 /tmp/prosim-gen.json)
  echo "$status"
  if grep -q "200" <<< "$status"; then
    echo "Generate OK. Response preview:"
    sed '$d' /tmp/prosim-gen.json | head -c 500
  else
    echo "Response:"
    sed '$d' /tmp/prosim-gen.json
  fi
else
  echo "Request failed (timeout or connection refused)"
fi
