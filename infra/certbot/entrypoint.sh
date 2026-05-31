#!/bin/sh
set -e

DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@example.com}"
WEBROOT="/var/www/certbot"

echo "Certbot manager started for domain: $DOMAIN"
echo "Email: $EMAIL"

# Wait a bit for nginx to be ready (so webroot is accessible)
sleep 5

# Check if certificate already exists
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "No certificate found for $DOMAIN. Requesting new certificate..."
    certbot certonly \
        --webroot \
        -w "$WEBROOT" \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        || echo "Certificate request failed. Will retry on next check."
else
    echo "Certificate already exists for $DOMAIN"
fi

# Signal nginx to reload if we got a cert
if [ -d "/etc/letsencrypt/live/$DOMAIN" ] && [ -f "/etc/letsencrypt/.reload-nginx" ]; then
    echo "Triggering nginx reload..."
fi

# Auto-renewal loop
echo "Starting auto-renewal loop (every 12 hours)..."
while :; do
    echo "Checking certificate renewal at $(date)"
    certbot renew \
        --quiet \
        --webroot \
        -w "$WEBROOT" \
        --deploy-hook 'touch /etc/letsencrypt/.reload-nginx' \
        || true
    sleep 12h
done
