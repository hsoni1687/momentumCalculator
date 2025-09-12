#!/bin/bash

echo "🔧 Fixing 502 errors for /strategies endpoint..."

# Restart nginx to refresh upstream connections
echo "🔄 Restarting nginx..."
docker-compose -f docker-compose-microservices.yml restart nginx

# Wait a moment for nginx to fully start
sleep 3

# Test the endpoint
echo "🧪 Testing /strategies endpoint..."
if curl -s http://localhost/strategies > /dev/null; then
    echo "✅ SUCCESS: /strategies endpoint is working!"
    echo "🚀 You can now use http://localhost:3001 without 502 errors"
else
    echo "❌ Still having issues. Let's restart strategy service too..."
    docker-compose -f docker-compose-microservices.yml restart strategy-service nginx
    sleep 5
    
    if curl -s http://localhost/strategies > /dev/null; then
        echo "✅ SUCCESS: /strategies endpoint is working after service restart!"
    else
        echo "❌ FAILED: Please check docker logs with:"
        echo "   docker-compose -f docker-compose-microservices.yml logs nginx"
        echo "   docker-compose -f docker-compose-microservices.yml logs strategy-service"
    fi
fi
