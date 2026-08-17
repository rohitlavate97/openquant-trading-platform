from decimal import Decimal
import pytest

from openquant.adapters.brokers.angelone_adapter import AngelOneSmartAPIAdapter
from openquant.adapters.brokers.certification_harness import BrokerAdapterCertificationHarness
from openquant.domain.models.order import Order, OrderSide, OrderType, TimeInForce


@pytest.mark.asyncio
async def test_angelone_adapter_certification():
    adapter = AngelOneSmartAPIAdapter(is_sandbox=True)
    report = await BrokerAdapterCertificationHarness.run_certification_audit(adapter)
    assert report.is_certified is True
    assert report.live_trading_eligible is True
    assert adapter.is_certified is True


@pytest.mark.asyncio
async def test_angelone_adapter_order_and_positions():
    adapter = AngelOneSmartAPIAdapter(is_sandbox=True)
    await adapter.connect({"mock_auth": "true"})

    order = Order(
        order_id="ord_ao_1",
        account_id="A123456",
        broker_id=adapter.adapter_id,
        strategy_id="strat_test",
        symbol="RELIANCE",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.DAY,
        quantity=Decimal("50"),
        price=Decimal("2500.00"),
        idempotency_key="idem_ao_1",
    )

    report = await adapter.place_order(order)
    assert report.broker_order_id.startswith("ao_")
    assert report.filled_quantity == Decimal("50")

    positions = await adapter.get_positions("A123456")
    assert len(positions) == 1
    assert positions[0].symbol == "RELIANCE"

    funds = await adapter.get_funds("A123456")
    assert funds.currency == "INR"
    assert funds.available_cash == Decimal("200000.00")

    holdings = await adapter.get_holdings("A123456")
    assert len(holdings) >= 1

    instruments = await adapter.download_instruments()
    assert len(instruments) >= 2
