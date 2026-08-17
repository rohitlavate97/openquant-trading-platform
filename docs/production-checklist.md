# OpenQuant Production Readiness Checklist

Before authorizing live capital trading in production, complete this 10-point readiness checklist.

---

## Preflight Verification Matrix

- [ ] **1. Cryptographic Secrets Rotation**
  - Unique `JWT_SECRET_KEY` (64 hex characters) generated and securely stored.
  - Unique `OPENQUANT_MASTER_SECRET` derived and backed up in offsite secrets vault.
  - Default database & Redis passwords replaced with high-entropy credentials.

- [ ] **2. Database & Data Persistence**
  - PostgreSQL 16 initialized with WAL archiving and daily automated backup cron.
  - Redis 7.2 configured with AOF (`appendonly yes`) on persistent block storage.
  - Alembic migrations executed up to the latest revision.

- [ ] **3. Network & Transport Security**
  - HTTPS / TLS 1.3 enforced on all external endpoints.
  - WebSockets upgraded over `wss://` with reverse proxy keep-alive timeouts $\ge 86400\text{s}$.
  - Internal database & Redis ports blocked by firewall / bound exclusively to Docker bridge network.

- [ ] **4. Pre-Trade Risk Engine Calibration**
  - Maximum daily loss limit configured (default: 3.0%).
  - Maximum peak drawdown threshold configured (default: 5.0%).
  - Pre-trade market data staleness limit set to $\le 3000\text{ms}$ (Rule 7).
  - Rate limiting configured (default: 10 orders/sec).

- [ ] **5. Broker Adapter Certification (Rule 9)**
  - All broker adapters passed 5-point automated certification test.
  - Credentials encrypted with PBKDF2 AES-Fernet vault.
  - Real-time order routing verified in broker sandbox/paper mode first.

- [ ] **6. 7-Stage Promotion Gate Enforcement (Rule 1)**
  - Live trading prohibited for un-promoted strategies.
  - All live strategies have completed Out-of-Sample Walk-Forward Backtesting and Paper Trading stages.

- [ ] **7. Emergency Kill Switch Drill**
  - Verified 1-click Global Kill Switch triggers immediate trading halt.
  - Position flattening mechanism verified with paper broker.

- [ ] **8. State Reconciliation Active (Rule 5)**
  - Periodic reconciliation scheduled every 60 seconds.
  - Automatic trading halt interlock enabled on position quantity mismatch.

- [ ] **9. Observability & Alerting**
  - Prometheus scraping `/metrics` without timeouts.
  - Grafana dashboards imported and verified.
  - Critical alert channels (Telegram, Discord, Email, Webhook) configured with test notifications delivered.

- [ ] **10. Disaster Recovery Runbook**
  - Daily `pg_dump` backup schedule tested with a mock database restore drill.
  - Master encryption keys archived in secondary secure location.
