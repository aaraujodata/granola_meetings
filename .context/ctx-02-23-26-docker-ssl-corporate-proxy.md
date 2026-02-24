# Docker SSL/TLS Trust for Corporate Proxies

## Problem

Docker containers fail HTTPS requests with:
```
SSLCertVerificationError: certificate verify failed: unable to get local issuer certificate
```

This happens because corporate SSL-inspection proxies (Zscaler, NortonLifeLock, etc.) intercept TLS traffic and re-sign it with their own CA certificate. The `python:3.12-slim` Docker image doesn't have these corporate CAs in its trust store.

## Root Cause Chain

1. Corporate network runs a TLS-inspection proxy (e.g., Zscaler)
2. Proxy intercepts HTTPS connections and presents its own certificate signed by a corporate CA (e.g., `NortonLifeLock Inc. Private SSL Inspection ICA`)
3. Inside Docker, Python's `requests`/`urllib3` verifies the certificate chain against `certifi`'s CA bundle
4. The corporate CA is not in `certifi`'s bundle → `CERTIFICATE_VERIFY_FAILED`

You can confirm this by running inside the container:
```bash
docker compose exec worker openssl s_client -connect api.granola.ai:443 -brief 2>&1 | head -5
```
If you see an issuer like `Zscaler Inc.` or `NortonLifeLock`, a proxy is intercepting.

## Solution Architecture

### Files

| File | Purpose |
|------|---------|
| `.ca-certs/` | Directory where users drop corporate CA `.pem` files |
| `web/backend/docker-entrypoint.sh` | Entrypoint script that builds combined CA bundle at container startup |
| `docker-compose.yml` | Mounts `.ca-certs/` into backend and worker containers |

### How It Works

1. User drops their corporate CA PEM file into `.ca-certs/` (e.g., `.ca-certs/corporate-ca.pem`)
2. At container startup, `docker-entrypoint.sh` checks for `.pem` files in `/app/.ca-certs/`
3. If found, it builds a combined bundle: `certifi` public CAs + all custom CAs
4. Sets `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` env vars pointing to the combined bundle
5. If no `.pem` files exist, the entrypoint passes through silently (no-op)

### Entrypoint Logic

```bash
# Check for PEM files → build combined bundle → set env vars → exec CMD
if ls "$CA_DIR"/*.pem; then
    python -c "import certifi; print(certifi.where())" | xargs cat > "$BUNDLE"
    for cert in "$CA_DIR"/*.pem; do cat "$cert" >> "$BUNDLE"; done
    export SSL_CERT_FILE="$BUNDLE"
    export REQUESTS_CA_BUNDLE="$BUNDLE"
fi
exec "$@"
```

## Setup Instructions

### Quick Setup (Zscaler/NortonLifeLock on macOS)

```bash
make setup-ssl        # Exports corporate CA from macOS system keychain
make down && make up   # Rebuild containers with the CA bundle
```

### Manual Setup (any corporate CA)

1. Get your corporate root CA PEM file from IT (or export it from macOS Keychain Access)
2. Copy it into the project:
   ```bash
   cp /path/to/your-corporate-ca.pem .ca-certs/
   ```
3. Rebuild containers:
   ```bash
   make down && make up
   ```

### Exporting from macOS Keychain

To find and export corporate CAs manually:
```bash
# List corporate certificates in system keychain
security find-certificate -a -c "NortonLifeLock" /Library/Keychains/System.keychain

# Export as PEM
security find-certificate -a -c "NortonLifeLock" -p /Library/Keychains/System.keychain > .ca-certs/corporate-ca.pem
```

Replace `"NortonLifeLock"` with your corporate CA's common name (visible in Keychain Access → System → Certificates).

### Verification

After `make up`, check the worker logs:
```bash
docker compose logs worker 2>&1 | head -5
```

Expected output:
```
worker-1  | Custom CA certificates detected, building combined bundle...
worker-1  |   Added: corporate-ca.pem
worker-1  | CA bundle ready at /tmp/combined-ca-bundle.pem
```

Test from inside the container:
```bash
docker compose exec worker python -c "import requests; print(requests.get('https://api.granola.ai').status_code)"
```

## Environment Variables Set by Entrypoint

| Variable | Used By | Purpose |
|----------|---------|---------|
| `SSL_CERT_FILE` | Python `ssl` stdlib | Default CA file for all Python SSL connections |
| `REQUESTS_CA_BUNDLE` | `requests` / `urllib3` | CA bundle for the `requests` library |

## Important Notes

- `.ca-certs/*.pem` files are gitignored (the global `*.pem` pattern in `.gitignore` covers them)
- The `.ca-certs/` directory is mounted read-only (`:ro`) into containers
- The combined bundle is built fresh at every container start (picks up CA rotations automatically)
- If no `.pem` files are present, the entrypoint is a no-op — no impact on machines without a proxy
- Multiple `.pem` files can be placed in `.ca-certs/` — all will be appended to the bundle
- The `certifi` package (bundled with `requests`) provides the base public CA roots

## Troubleshooting

### SSL still fails after adding PEM
- Verify the PEM file is a valid certificate: `openssl x509 -in .ca-certs/your-ca.pem -text -noout`
- Make sure it's the **root CA**, not a leaf/intermediate cert
- Containers must be recreated (`make down && make up`), not just restarted

### Don't know which CA to export
Run this inside the container to see who signed the intercepted cert:
```bash
docker compose exec worker openssl s_client -connect api.granola.ai:443 -brief 2>&1 | grep -i issuer
```
Then search your macOS keychain for that issuer name.

### Host-side CLI (outside Docker)
For the pipeline CLI running directly on the host (`python granola_pipeline.py ...`), macOS typically trusts the corporate CA through its system keychain. If not, follow the same `SSL_CERT_FILE` approach in your shell profile:
```bash
export SSL_CERT_FILE="$HOME/.ca-bundles/company_bundle.pem"
export REQUESTS_CA_BUNDLE="$HOME/.ca-bundles/company_bundle.pem"
```
