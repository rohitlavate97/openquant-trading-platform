# OpenQuant Self-Hosting & Production Deployment Guide

This guide provides step-by-step instructions for deploying and operating the **OpenQuant Algorithmic Trading Platform** in production environments.

---

## 1. System Requirements & Hardware Sizing

| Tier | Workload Profile | Minimum CPU | Minimum RAM | Storage |
|:---|:---|:---:|:---:|:---|
| **Standard** | Up to 10 active strategies, L1 market feeds, 5 brokers | 4 Cores | 8 GB | 50 GB NVMe SSD |
| **High-Frequency / Multi-Asset** | 50+ strategies, L2 order books, tick-level ML backtests | 8–16 Cores | 32 GB | 250 GB NVMe SSD |
| **Enterprise High-Availability** | Redundant nodes, Kubernetes cluster, clustered DB | 16+ Cores | 64 GB | 500 GB NVMe SSD |

*Recommended OS*: Ubuntu 22.04 LTS / 24.04 LTS or Debian 12.

---

## 2. Deployment Method A: Production Docker Compose (Recommended for VMs)

### Step 1: Clone Repository & Create Production Environment File
```bash
git clone https://github.com/rohitlavate97/openquant-trading-platform.git /opt/openquant
cd /opt/openquant

# Copy production environment template
cp .env.production.example .env.production
chmod 600 .env.production
```

### Step 2: Generate Cryptographic Secrets
Generate secure random keys for your production environment:
```bash
# JWT Secret
JWT_SECRET=$(openssl rand -hex 32)
sed -i "s/replace_with_secure_random_jwt_secret_key_hex_64_chars/$JWT_SECRET/" .env.production

# PostgreSQL Password
DB_PASS=$(openssl rand -base64 24)
sed -i "s/replace_with_strong_database_password_32_chars_min/$DB_PASS/" .env.production

# Redis Password
REDIS_PASS=$(openssl rand -base64 24)
sed -i "s/replace_with_strong_redis_password_32_chars_min/$REDIS_PASS/" .env.production

# Master Fernet Vault Key
MASTER_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s/replace_with_secure_production_fernet_master_vault_key/$MASTER_SECRET/" .env.production
```

> [!CAUTION]
> Store your `OPENQUANT_MASTER_SECRET` in an offsite password vault (e.g. 1Password, HashiCorp Vault, AWS Secrets Manager). If lost, broker credentials cannot be decrypted!

### Step 3: Launch Production Containers
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### Step 4: Verify Container Health & Services
```bash
docker compose -f docker-compose.prod.yml ps
```
All containers (`postgres`, `redis`, `backend`, `frontend`, `prometheus`, `grafana`) should report `(healthy)`.

---

## 3. Deployment Method B: Kubernetes (Helm 3.x)

### Step 1: Create Kubernetes Namespace & Ingress TLS Secret
```bash
kubectl create namespace openquant

# Optional: Add TLS Secret (or let cert-manager provision it)
kubectl create secret tls openquant-tls-certs \
  --cert=/path/to/fullchain.pem \
  --key=/path/to/privkey.pem \
  -n openquant
```

### Step 2: Install via Helm
```bash
cd /opt/openquant/deployments/helm/openquant

helm upgrade --install openquant . \
  --namespace openquant \
  --values values.yaml \
  --set backend.secrets.jwtSecret="$JWT_SECRET" \
  --set backend.secrets.masterSecret="$MASTER_SECRET"
```

### Step 3: Monitor Pod Rollout & Horizontal Pod Autoscaler
```bash
kubectl get pods -n openquant -w
kubectl get hpa -n openquant
```

---

## 4. HTTPS & Domain SSL Setup (Certbot & Nginx Reverse Proxy)

If deploying directly on a Linux host with Nginx and Certbot:

```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx

# Obtain SSL Certificate
sudo certbot --nginx -d trading.yourdomain.com
```

Sample Nginx reverse proxy configuration (`/etc/nginx/sites-available/openquant`):
```nginx
server {
    server_name trading.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/trading.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trading.yourdomain.com/privkey.pem;
}
```

---

## 5. Observability & Monitoring Access

- **Prometheus Metrics**: `http://localhost:9090` (Scraping `/metrics` every 5 seconds).
- **Grafana Dashboard**: `http://localhost:3000`
  - Default User: `admin`
  - Pre-loaded Dashboards:
    - *Trading Operations Dashboard*: Execution latencies, order status rates, fill volumes.
    - *Risk Controls & Hard Stops*: Kill switch status, daily loss limits, drawdown trackers.
    - *Market Data & Feed Health*: Feed latency, tick rates, staleness guard status.
