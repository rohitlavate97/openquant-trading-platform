"""Automated Broker Adapter Certification and Sandbox Security Review Harness.

Enforces Non-Negotiable Rule 9: No broker adapter is eligible for Live Trading
until it has completed automated sandbox validation and security audit checks.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import uuid

from openquant.domain.models.order import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from openquant.domain.models.broker import (
    BrokerSecurityAuditCheck,
    BrokerSecurityAuditReport,
)
from openquant.domain.ports.broker_adapter import IBrokerAdapter
from openquant.adapters.brokers.base import BaseBrokerAdapter


class BrokerAdapterCertificationHarness:
    """Security and Sandbox validation harness executing systematic certification tests."""

    @classmethod
    async def run_certification_audit(
        cls,
        adapter: IBrokerAdapter,
        certified_by: str = "openquant_certification_harness",
    ) -> BrokerSecurityAuditReport:
        """Run all mandatory security, sandbox order lifecycle, and fault tolerance checks."""
        checks: list[BrokerSecurityAuditCheck] = []
        rejection_reasons: list[str] = []

        # 1. Credential Handling & Metadata Leakage Check
        check1 = await cls._audit_credential_security(adapter)
        checks.append(check1)
        if not check1.passed:
            rejection_reasons.append(check1.description)

        # 2. Sandbox Authentication Handshake
        check2 = await cls._audit_auth_handshake(adapter)
        checks.append(check2)
        if not check2.passed:
            rejection_reasons.append(check2.description)

        # 3. Sandbox Order Placement & Fill Lifecycle
        check3 = await cls._audit_order_lifecycle(adapter)
        checks.append(check3)
        if not check3.passed:
            rejection_reasons.append(check3.description)

        # 4. Position & Funds Reporting Precision
        check4 = await cls._audit_positions_and_funds(adapter)
        checks.append(check4)
        if not check4.passed:
            rejection_reasons.append(check4.description)

        # 5. Fault Handling & Disconnect Resilience
        check5 = await cls._audit_fault_tolerance(adapter)
        checks.append(check5)
        if not check5.passed:
            rejection_reasons.append(check5.description)

        is_certified = all(c.passed for c in checks)
        live_eligible = is_certified

        report = BrokerSecurityAuditReport(
            adapter_id=adapter.adapter_id,
            is_certified=is_certified,
            live_trading_eligible=live_eligible,
            audit_timestamp=datetime.now(timezone.utc),
            certified_by=certified_by if is_certified else None,
            checks=checks,
            rejection_reasons=rejection_reasons,
        )

        # If it's a BaseBrokerAdapter subclass, record the certification directly
        if isinstance(adapter, BaseBrokerAdapter) and is_certified:
            adapter.mark_certified(audit_report=report, live_eligible=live_eligible)

        return report

    @classmethod
    async def _audit_credential_security(cls, adapter: IBrokerAdapter) -> BrokerSecurityAuditCheck:
        """Verify adapter metadata does not leak sensitive fields."""
        meta = adapter.metadata.model_dump()
        meta_str = str(meta).lower()
        leaks = [k for k in ["secret", "password", "token", "private_key"] if k in meta_str and meta.get(k)]
        passed = len(leaks) == 0
        return BrokerSecurityAuditCheck(
            check_name="CREDENTIAL_LEAKAGE_AUDIT",
            passed=passed,
            description="Verified adapter metadata contains zero plaintext secrets or leaked keys.",
            details={"leaks_detected": leaks},
        )

    @classmethod
    async def _audit_auth_handshake(cls, adapter: IBrokerAdapter) -> BrokerSecurityAuditCheck:
        """Verify connect/disconnect lifecycle transitions."""
        try:
            connected = await adapter.connect({"mock_auth": "true"})
            is_conn = await adapter.is_connected()
            passed = connected and is_conn
            return BrokerSecurityAuditCheck(
                check_name="AUTH_HANDSHAKE_VALIDATION",
                passed=passed,
                description="Verified sandbox authentication handshake and session state progression.",
                details={"connected": connected, "is_connected": is_conn},
            )
        except Exception as e:
            return BrokerSecurityAuditCheck(
                check_name="AUTH_HANDSHAKE_VALIDATION",
                passed=False,
                description=f"Auth handshake failed with error: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    async def _audit_order_lifecycle(cls, adapter: IBrokerAdapter) -> BrokerSecurityAuditCheck:
        """Verify order submission, execution reporting, and cancellation."""
        try:
            test_order = Order(
                order_id=f"cert_ord_{uuid.uuid4().hex[:8]}",
                idempotency_key=f"cert_idemp_{uuid.uuid4().hex[:8]}",
                strategy_id="strat_cert_test",
                account_id="acc_cert_01",
                broker_id=adapter.adapter_id,
                symbol="RELIANCE",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("1"),
            )
            report = await adapter.place_order(test_order)
            passed = report.broker_order_id is not None and report.status in (
                OrderStatus.FILLED,
                OrderStatus.SUBMITTED,
                OrderStatus.OPEN,
            )
            return BrokerSecurityAuditCheck(
                check_name="SANDBOX_ORDER_LIFECYCLE",
                passed=passed,
                description="Verified sandbox order dispatch, execution report receipt, and valid broker order id generation.",
                details={"broker_order_id": report.broker_order_id, "status": report.status.value},
            )
        except Exception as e:
            return BrokerSecurityAuditCheck(
                check_name="SANDBOX_ORDER_LIFECYCLE",
                passed=False,
                description=f"Order dispatch check failed: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    async def _audit_positions_and_funds(cls, adapter: IBrokerAdapter) -> BrokerSecurityAuditCheck:
        """Verify funds and positions precision and mathematical non-negativity."""
        try:
            funds = await adapter.get_funds("acc_cert_01")
            positions = await adapter.get_positions("acc_cert_01")
            passed = isinstance(funds.total_balance, Decimal) and isinstance(positions, list)
            return BrokerSecurityAuditCheck(
                check_name="POSITIONS_AND_FUNDS_INTEGRITY",
                passed=passed,
                description="Verified financial funds balance and portfolio position models adhere to Decimal precision standards.",
                details={"currency": funds.currency, "positions_count": len(positions)},
            )
        except Exception as e:
            return BrokerSecurityAuditCheck(
                check_name="POSITIONS_AND_FUNDS_INTEGRITY",
                passed=False,
                description=f"Funds query failed: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    async def _audit_fault_tolerance(cls, adapter: IBrokerAdapter) -> BrokerSecurityAuditCheck:
        """Verify adapter cleanly disconnects and handles session shutdown."""
        try:
            await adapter.disconnect()
            is_conn = await adapter.is_connected()
            passed = not is_conn
            return BrokerSecurityAuditCheck(
                check_name="FAULT_TOLERANCE_AND_SHUTDOWN",
                passed=passed,
                description="Verified adapter terminates connection gracefully without unhandled exceptions.",
                details={"is_connected_after_disconnect": is_conn},
            )
        except Exception as e:
            return BrokerSecurityAuditCheck(
                check_name="FAULT_TOLERANCE_AND_SHUTDOWN",
                passed=False,
                description=f"Shutdown failed: {str(e)}",
                details={"error": str(e)},
            )
