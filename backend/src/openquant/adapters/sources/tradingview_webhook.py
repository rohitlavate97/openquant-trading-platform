"""TradingView Alert Webhook Handler with HMAC-SHA256 signature and Replay Protection."""

import hmac
import hashlib
import time
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any

from openquant.domain.models.strategy_sources import (
    TradingViewAction,
    TradingViewWebhookPayload,
    TradingViewWebhookResult,
)
from openquant.domain.models.order import OrderRequest, OrderSide, OrderType, TimeInForce
from openquant.domain.ports.strategy_sources_port import ITradingViewWebhookHandler
from openquant.application.services.order_service import order_service, OrderManagementService
from openquant.application.services.audit_service import audit_log_service, AuditLogService

logger = logging.getLogger(__name__)


class TradingViewWebhookHandler(ITradingViewWebhookHandler):
    """Secure webhook adapter verifying HMAC signatures and executing alerts through OMS."""

    def __init__(
        self,
        oms: OrderManagementService | None = None,
        audit: AuditLogService | None = None,
        default_secret: str = "openquant_tv_secret_key",
        max_clock_skew_seconds: int = 60,
    ) -> None:
        self._oms: OrderManagementService = oms or order_service
        self._audit: AuditLogService = audit or audit_log_service
        self._default_secret = default_secret
        self._max_clock_skew = max_clock_skew_seconds
        self._seen_nonces: dict[str, float] = {}

    def _verify_hmac_signature(self, payload: TradingViewWebhookPayload, secret: str) -> bool:
        """Verify HMAC-SHA256 signature over canonical payload."""
        if not payload.signature:
            # Fallback to passphrase comparison if signature omitted
            return payload.passphrase == secret

        message = f"{payload.strategy_id}:{payload.ticker}:{payload.action}:{payload.contracts}:{payload.nonce}:{payload.timestamp}"
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_sig, payload.signature)

    def _check_replay_and_nonce(self, nonce: str, timestamp: int) -> tuple[bool, str]:
        """Check for clock skew and replay attacks."""
        current_time = int(time.time())
        if abs(current_time - timestamp) > self._max_clock_skew:
            return False, f"Timestamp rejected: clock skew {abs(current_time - timestamp)}s > {self._max_clock_skew}s"

        # Cleanup nonces older than 2x clock skew
        cutoff = time.time() - (self._max_clock_skew * 2)
        self._seen_nonces = {n: t for n, t in self._seen_nonces.items() if t > cutoff}

        if nonce in self._seen_nonces:
            return False, f"Replay attack detected: Nonce '{nonce}' has already been processed"

        self._seen_nonces[nonce] = time.time()
        return True, "OK"

    async def verify_and_process_webhook(
        self,
        payload: TradingViewWebhookPayload,
        secret_key: str | None = None,
    ) -> TradingViewWebhookResult:
        """Verify HMAC signature & nonce TTL, then submit order via OMS."""
        secret = secret_key or self._default_secret

        # 1. Replay & Nonce Verification
        valid_nonce, nonce_msg = self._check_replay_and_nonce(payload.nonce, payload.timestamp)
        if not valid_nonce:
            logger.warning("TradingView Webhook Rejected (Replay Guard): %s", nonce_msg)
            return TradingViewWebhookResult(success=False, message=nonce_msg)

        # 2. HMAC Signature Verification
        if not self._verify_hmac_signature(payload, secret):
            logger.warning("TradingView Webhook Rejected: Invalid HMAC signature for strategy '%s'", payload.strategy_id)
            return TradingViewWebhookResult(success=False, message="Invalid HMAC-SHA256 signature or passphrase")

        # 3. Translate to OrderRequest
        side = OrderSide.BUY if payload.action == TradingViewAction.BUY else OrderSide.SELL
        order_req = OrderRequest(
            account_id=payload.account_id,
            broker_id=payload.broker_id,
            strategy_id=payload.strategy_id,
            symbol=payload.ticker.upper(),
            side=side,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.GTC,
            quantity=payload.contracts,
            price=payload.price,
            idempotency_key=f"tv_{payload.nonce}",
        )

        # 4. Submit to OMS (synchronous pre-trade risk evaluation occurs here)
        try:
            order = await self._oms.submit_order(order_req)
            await self._audit.log_event(
                event_type="TRADINGVIEW_WEBHOOK_EXECUTED",
                actor_id="tradingview_webhook",
                entity_type="ORDER",
                entity_id=order.order_id,
                action="SUBMIT_ORDER",
                payload={"strategy_id": payload.strategy_id, "symbol": payload.ticker, "action": payload.action},
            )
            return TradingViewWebhookResult(
                success=True,
                order_id=order.order_id,
                message=f"Order '{order.order_id}' successfully submitted via TradingView alert",
            )
        except Exception as e:
            logger.error("TradingView Webhook Order Execution Failed: %s", e)
            return TradingViewWebhookResult(
                success=False,
                message=f"Risk/OMS Submission Failed: {str(e)}",
            )


# Global singleton webhook handler
tradingview_webhook_handler = TradingViewWebhookHandler()
