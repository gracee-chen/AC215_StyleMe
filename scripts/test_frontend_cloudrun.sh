#!/bin/bash
# Test Frontend Connection to Cloud Run
# This script helps test if the frontend can connect to Cloud Run backend

set -e

CLOUD_RUN_URL="https://styleme-inference-nty2g5pcpa-uc.a.run.app"

echo "🧪 Testing Frontend Connection to Cloud Run"
echo "============================================"
echo ""
echo "Cloud Run URL: ${CLOUD_RUN_URL}"
echo ""

# Test health endpoint
echo "1️⃣  Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${CLOUD_RUN_URL}/health")
HTTP_STATUS=$(echo "$HEALTH_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed!"
    echo "Response: $RESPONSE_BODY"
else
    echo "❌ Health check failed!"
    echo "HTTP Status: $HTTP_STATUS"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

echo ""
echo "✅ Cloud Run backend is accessible!"
echo ""
echo "📋 Next Steps:"
echo "1. Start frontend dev server:"
echo "   cd frontend && npm run dev"
echo ""
echo "2. Open browser to the URL shown (usually http://localhost:3000)"
echo ""
echo "3. Test features:"
echo "   - Upload images"
echo "   - View wardrobe"
echo "   - Get recommendations"
echo ""

