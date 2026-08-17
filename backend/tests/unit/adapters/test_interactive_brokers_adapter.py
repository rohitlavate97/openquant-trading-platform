from decimal import Decimal
import pytest

from openquant.adapters.brokers.interactive_brokers_adapter import InteractiveBrokersAdapter
from openquant.adapters.brokers.certification_harness import BrokerAdapterCertificationHarness
from openquant.domain.models.order import Order, OrderSide, OrderType, TimeInForce


@pytest.mark.asyncio
async def test_interactive_brokers_adapter_certification():
    adapter = InteractiveBrokersAdapter(is_sandbox=True)
    report = await BrokerAdapterCertificationHarness.run_certification_audit(adapter)
    assert report.is_certified is True
    assert report.live_trading_eligible is True
    assert adapter.is_certified is True


@pytest.mark.asyncio
async def test_interactive_brokers_adapter_order_and_positions():
    adapter = InteractiveBrokersAdapter(is_sandbox=True)
    await adapter.connect({"mock_auth": "true"})

    order = Order(
        order_id="ord_ib_1",
        account_id="U1234567",
        broker_id=adapter.adapter_id,
        strategy_id="strat_test",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.DAY,
        quantity=Decimal("100"),
        price=Decimal("155.00"),
        idempotency_key="idem_ib_1",
    )

    report = await adapter.place_order(order)
    assert report.broker_order_id.startswith("ib_")
    assert report.filled_quantity == Decimal("100")

    positions = await adapter.get_positions("U1234567")
    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"

    funds = await adapter.get_funds("U1234567")
    assert funds.currency == "USD"
    assert funds.available_cash == Decimal("500000.00")

    holdings = await adapter.get_holdings("U1234567")
    assert len(holdings) >= 1

    instruments = await adapter.download_instruments()
    assert len(instruments) >= 2
