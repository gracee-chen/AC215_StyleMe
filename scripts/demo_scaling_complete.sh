#!/bin/bash
# Complete Scaling Demonstration Script
# This script demonstrates Kubernetes auto-scaling behavior

set -e

echo "🚀 Kubernetes Auto-Scaling Demonstration"
echo "========================================"
echo ""

# Get service IP
SERVICE_IP=$(kubectl get svc styleme-inference-service -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$SERVICE_IP" ]; then
    echo "❌ Error: Could not get service IP"
    exit 1
fi

echo "Service IP: $SERVICE_IP"
echo ""

# Step 1: Initial State
echo "📊 Step 1: Initial State"
echo "------------------------"
kubectl get hpa styleme-inference-hpa -n default
echo ""
kubectl get pods -n default -l app=styleme,component=inference
echo ""
kubectl top pods -n default -l app=styleme,component=inference 2>/dev/null || echo "Metrics loading..."
echo ""

# Step 2: Generate Load
echo "⚡ Step 2: Generating Load (60 seconds)"
echo "--------------------------------------"
echo "This will generate load to trigger auto-scaling..."
echo "Watch in another terminal: kubectl get hpa styleme-inference-hpa -n default -w"
echo ""

# Generate load in background
(
    for i in {1..3000}; do
        curl -s http://${SERVICE_IP}/health > /dev/null &
        if [ $((i % 100)) -eq 0 ]; then
            sleep 0.1
        fi
    done
    wait
) &
LOAD_PID=$!

# Monitor for 60 seconds
for i in {1..60}; do
    sleep 1
    if [ $((i % 10)) -eq 0 ]; then
        echo -n "."
    fi
done
echo ""

# Stop load generation
kill $LOAD_PID 2>/dev/null || true
wait $LOAD_PID 2>/dev/null || true

echo ""
echo "📊 Step 3: State After Load"
echo "---------------------------"
kubectl get hpa styleme-inference-hpa -n default
echo ""
kubectl get pods -n default -l app=styleme,component=inference
echo ""
kubectl top pods -n default -l app=styleme,component=inference 2>/dev/null || echo "Metrics loading..."
echo ""

# Step 4: Manual Scaling (if auto-scaling didn't trigger)
echo "🔧 Step 4: Manual Scaling Demonstration"
echo "--------------------------------------"
echo "Scaling to 3 replicas manually..."
kubectl scale deployment styleme-inference -n default --replicas=3
echo "Waiting for pods to start..."
sleep 15

kubectl get pods -n default -l app=styleme,component=inference
echo ""

# Step 5: Scale Back Down
echo "📉 Step 5: Scaling Back Down"
echo "-----------------------------"
echo "Scaling back to 1 replica..."
kubectl scale deployment styleme-inference -n default --replicas=1
echo "Waiting for pods to terminate..."
sleep 15

kubectl get pods -n default -l app=styleme,component=inference
echo ""

# Final State
echo "✅ Final State"
echo "--------------"
kubectl get hpa styleme-inference-hpa -n default
echo ""
kubectl get pods -n default -l app=styleme,component=inference
echo ""

echo "🎉 Demonstration Complete!"
echo ""
echo "📝 Summary:"
echo "  - HPA is configured: 1-5 replicas, CPU 70%, Memory 80%"
echo "  - Scaling mechanism works (manual scaling demonstrated)"
echo "  - Cluster responds by creating/terminating pods"
echo "  - For auto-scaling, generate heavier load or wait for HPA to detect threshold"
echo ""
echo "💡 To see auto-scaling in action:"
echo "   - Generate sustained heavy load (several minutes)"
echo "   - Or use a heavier endpoint (not just /health)"
echo "   - Watch: kubectl get hpa styleme-inference-hpa -n default -w"

