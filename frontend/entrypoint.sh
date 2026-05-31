#!/bin/sh
set -e

DOMAIN=${DOMAIN:-localhost}
SSL_DIR="/etc/nginx/ssl"
LE_DIR="/etc/letsencrypt/live/$DOMAIN"

mkdir -p $SSL_DIR

if [ -f "$LE_DIR/fullchain.pem" ] && [ -f "$LE_DIR/privkey.pem" ]; then
    echo "Using Let's Encrypt certificates for $DOMAIN"
    cp "$LE_DIR/fullchain.pem" "$SSL_DIR/cert.pem"
    cp "$LE_DIR/privkey.pem" "$SSL_DIR/key.pem"
else
    echo "No Let's Encrypt certs found, generating self-signed for $DOMAIN"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/CN=$DOMAIN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1"
fi

# Substitute env vars in nginx template
envsubst '${API_GATEWAY_URL} ${DOMAIN}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Background: watch for cert renewal trigger and reload nginx
(
    while :; do
        if [ -f /etc/letsencrypt/.reload-nginx ]; then
            rm -f /etc/letsencrypt/.reload-nginx
            echo "Certificates updated, reloading nginx..."
            if [ -f "$LE_DIR/fullchain.pem" ] && [ -f "$LE_DIR/privkey.pem" ]; then
                cp "$LE_DIR/fullchain.pem" "$SSL_DIR/cert.pem"
                cp "$LE_DIR/privkey.pem" "$SSL_DIR/key.pem"
            fi
            nginx -s reload || true
        fi
        sleep 60
    done
) &

exec "$@"
