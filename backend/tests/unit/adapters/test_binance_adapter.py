from decimal import Decimal
import pytest

from openquant.adapters.brokers.binance_adapter import BinanceCryptoAdapter
from openquant.adapters.brokers.certification_harness import BrokerAdapterCertificationHarness
from openquant.domain.models.order import Order, OrderSide, OrderType, TimeInForce


@pytest.mark.asyncio
async def test_binance_adapter_certification():
    adapter = BinanceCryptoAdapter(is_sandbox=True)
    report = await BrokerAdapterCertificationHarness.run_certification_audit(adapter)
    assert report.is_certified is True
    assert report.live_trading_eligible is True
    assert adapter.is_certified is True


@pytest.mark.asyncio
async def test_binance_adapter_order_and_positions():
    adapter = BinanceCryptoAdapter(is_sandbox=True)
    await adapter.connect({"mock_auth": "true"})

    order = Order(
        order_id="ord_bin_1",
        account_id="binance_main",
        broker_id=adapter.adapter_id,
        strategy_id="strat_crypto",
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        quantity=Decimal("0.5"),
        price=Decimal("65000.00"),
        idempotency_key="idem_bin_1",
    )

    report = await adapter.place_order(order)
    assert report.broker_order_id.startswith("bin_")
    assert report.filled_quantity == Decimal("0.5")

    positions = await adapter.get_positions("binance_main")
    assert len(positions) == 1
    assert positions[0].symbol == "BTCUSDT"

    funds = await adapter.get_funds("binance_main")
    assert funds.currency == "USDT"
    assert funds.available_cash == Decimal("50000.00")

    holdings = await adapter.get_holdings("binance_main")
    assert len(holdings) >= 2

    instruments = await adapter.download_instruments()
    assert len(instruments) >= 2
