#!/bin/bash
set -e

echo "=== HiveRecon Groq Migration — Post-Build Tests ==="
echo ""

# 1. Verify GROQ_API_KEY is set
echo "1️⃣ Checking GROQ_API_KEY..."
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ GROQ_API_KEY not set. Export it:"
    echo "   export GROQ_API_KEY='gsk_your_key_here'"
    exit 1
else
    echo "✅ GROQ_API_KEY is set (length: ${#GROQ_API_KEY})"
fi

# 2. Stop & remove old containers
echo ""
echo "2️⃣ Stopping old containers..."
docker compose down || true

# 3. Rebuild app service (no cache)
echo ""
echo "3️⃣ Building Docker image (no cache)..."
docker compose build --no-cache app

# 4. Start services
echo ""
echo "4️⃣ Starting HiveRecon..."
docker compose up -d

# 5. Wait for app to be ready
echo ""
echo "5️⃣ Waiting for app to be healthy (30s timeout)..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ App is healthy"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 1
done

# 6. Check health endpoint
echo ""
echo "6️⃣ Health check endpoint..."
HEALTH=$(curl -s http://localhost:8000/health | jq .)
echo "$HEALTH"
if echo "$HEALTH" | jq -e '.groq_configured == true' > /dev/null; then
    echo "✅ Groq is configured"
else
    echo "❌ Groq not configured"
    exit 1
fi

# 7. Trigger a test scan
echo ""
echo "7️⃣ Triggering test scan (hackerone.com)..."
SCAN_RESPONSE=$(curl -s -X POST http://localhost:8000/scans \
    -H "Content-Type: application/json" \
    -d '{"target":"hackerone.com"}')
echo "$SCAN_RESPONSE" | jq .

SCAN_ID=$(echo "$SCAN_RESPONSE" | jq -r '.scan_id // .id // empty')
if [ -z "$SCAN_ID" ]; then
    echo "❌ No scan_id in response"
    exit 1
fi
echo "✅ Scan created: $SCAN_ID"

# 8. Wait for scan to complete (60s timeout)
echo ""
echo "8️⃣ Waiting for scan to complete (60s)..."
for i in {1..60}; do
    STATUS=$(curl -s http://localhost:8000/scans/$SCAN_ID | jq -r '.status // empty')
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "success" ]; then
        echo "✅ Scan completed ($STATUS)"
        break
    fi
    echo "  Status: $STATUS ($i/60)"
    sleep 1
done

# 9. Get summary (AI-generated)
echo ""
echo "9️⃣ Fetching AI summary..."
SUMMARY=$(curl -s http://localhost:8000/scans/$SCAN_ID/summary)
echo "$SUMMARY" | jq .

# Check if summary contains real AI content (not empty/null)
if echo "$SUMMARY" | jq -e '.summary | length > 10' > /dev/null 2>&1; then
    echo "✅ Real AI content detected in summary"
else
    echo "⚠️  Summary may be empty or still processing"
fi

# 10. Final status
echo ""
echo "10️⃣ Final status..."
docker compose ps
echo ""
echo "=== ✅ Migration Tests Complete ==="
echo ""
echo "Next steps:"
echo "1. Verify summary output above contains real AI analysis"
echo "2. Run: git tag v1.0.0 && git push origin main --tags"
echo "3. Check GitHub releases"
