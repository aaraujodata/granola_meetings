#!/bin/bash
set -e

CA_DIR="/app/.ca-certs"
BUNDLE="/tmp/combined-ca-bundle.pem"

# If custom CA certificates exist, build a combined bundle (certifi + corporate CAs)
if ls "$CA_DIR"/*.pem 1>/dev/null 2>&1; then
    echo "Custom CA certificates detected, building combined bundle..."
    # Start with certifi's public CA bundle
    python -c "import certifi; print(certifi.where())" | xargs cat > "$BUNDLE"
    # Append each custom CA
    for cert in "$CA_DIR"/*.pem; do
        echo "" >> "$BUNDLE"
        cat "$cert" >> "$BUNDLE"
        echo "  Added: $(basename "$cert")"
    done
    export SSL_CERT_FILE="$BUNDLE"
    export REQUESTS_CA_BUNDLE="$BUNDLE"
    echo "CA bundle ready at $BUNDLE"
fi

exec "$@"
