#!/bin/sh
set -e

DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@example.com}"
WEBROOT="/var/www/certbot"

echo "Certbot manager started for domain: $DOMAIN"
echo "Email: $EMAIL"

# Retry logic for first certificate request
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "No certificate found for $DOMAIN. Will request with retries..."
    
    for i in 1 2 3 4 5; do
        echo "Attempt $i/5: Requesting certificate..."
        
        if certbot certonly \
            --webroot \
            -w "$WEBROOT" \
            --non-interactive \
            --agree-tos \
            --email "$EMAIL" \
            -d "$DOMAIN"; then
            
            echo "Certificate obtained successfully!"
            touch /etc/letsencrypt/.reload-nginx
            break
        else
            echo "Attempt $i failed. Retrying in 15 seconds..."
            sleep 15
        fi
    done
    
    if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        echo "WARNING: Failed to obtain certificate after 5 attempts."
        echo "Will retry on next renewal cycle."
    fi
else
    echo "Certificate already exists for $DOMAIN"
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
