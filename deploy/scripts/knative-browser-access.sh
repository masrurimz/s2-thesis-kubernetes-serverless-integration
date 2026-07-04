#!/bin/bash

echo "=== Knative Browser Access Solutions ==="
echo ""

echo "🎯 The Issue:"
echo "Knative requires Host header: serverless-sim.default.localhost"
echo "Browsers can't easily add custom headers to requests"
echo ""

echo "✅ WORKING SOLUTIONS:"
echo ""

echo "🌐 Option 1: Add to /etc/hosts (EASIEST)"
echo "Setup:"
echo "  sudo bash -c 'echo \"127.0.0.1 serverless-sim.default.localhost\" >> /etc/hosts'"
echo "Access in browser:"
echo "  http://serverless-sim.default.localhost:8081"
echo "Benefits: Works in any browser, no extensions needed"
echo ""

echo "🔗 Option 2: Browser extension with headers"
echo "Setup:"
echo "  Chrome: Install 'ModHeader' extension"
echo "  Firefox: Install 'Modify Headers' extension"
echo "  Add header: Host = serverless-sim.default.localhost"
echo "Access in browser:"
echo "  http://localhost:8081"
echo "Benefits: No system changes needed"
echo ""

echo "🚀 Option 3: Command line tools"
echo "curl:"
echo "  curl -H 'Host: serverless-sim.default.localhost' http://localhost:8081"
echo "httpie:"
echo "  http localhost:8081 Host:serverless-sim.default.localhost"
echo "Benefits: Perfect for testing and development"
echo ""

echo "⚖️ Option 4: Through HAProxy (Already Working)"
echo "Access mixed traffic (80% K3s, 20% Knative):"
echo "  http://localhost:8082"
echo "Benefits: Shows hybrid system in action"
echo ""

if [[ "$1" == "--setup-hosts" ]]; then
    echo "Setting up /etc/hosts entry..."
    if sudo bash -c 'echo "127.0.0.1 serverless-sim.default.localhost" >> /etc/hosts'; then
        echo "✅ Success! You can now access:"
        echo "   http://serverless-sim.default.localhost:8081"
    else
        echo "❌ Failed to update /etc/hosts"
        echo "Try running: sudo bash -c 'echo \"127.0.0.1 serverless-sim.default.localhost\" >> /etc/hosts'"
    fi
elif [[ "$1" == "--test" ]]; then
    echo "Testing Knative access methods..."
    echo ""
    
    echo "1. Testing direct with headers:"
    if curl -s -H "Host: serverless-sim.default.localhost" http://localhost:8081 | grep -q "Knative"; then
        echo "   ✅ curl with headers works"
    else
        echo "   ❌ curl with headers failed"
    fi
    
    echo "2. Testing HAProxy route:"
    if curl -s http://localhost:8082 | grep -q "Backend Type"; then
        echo "   ✅ HAProxy route works"
    else
        echo "   ❌ HAProxy route failed"
    fi
    
    echo "3. Testing hosts file entry:"
    if grep -q "serverless-sim.default.localhost" /etc/hosts 2>/dev/null; then
        echo "   ✅ hosts file entry exists"
        if curl -s http://serverless-sim.default.localhost:8081 | grep -q "Knative" 2>/dev/null; then
            echo "   ✅ hosts file route works"
        else
            echo "   ⚠️ hosts file entry exists but route not working"
        fi
    else
        echo "   ⚠️ No hosts file entry found"
    fi
else
    echo "Usage:"
    echo "  $0                  # Show all options"
    echo "  $0 --setup-hosts   # Setup /etc/hosts entry"
    echo "  $0 --test          # Test all access methods"
    echo ""
    echo "🏆 RECOMMENDED: Use Option 1 (--setup-hosts) for easy browser access"
fi