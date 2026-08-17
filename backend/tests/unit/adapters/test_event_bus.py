import pytest
from openquant.adapters.event_bus.in_memory_event_bus import InMemoryEventBus


@pytest.mark.asyncio
async def test_in_memory_event_bus_pub_sub_and_wildcard():
    bus = InMemoryEventBus()
    received_exact = []
    received_wildcard = []

    async def exact_handler(data):
        received_exact.append(data)

    async def wildcard_handler(data):
        received_wildcard.append(data)

    await bus.subscribe("risk.kill_switch", exact_handler)
    await bus.subscribe("*", wildcard_handler)

    # 1. Publish to subscribed topic
    await bus.publish("risk.kill_switch", {"reason": "Drawdown stop"})
    assert len(received_exact) == 1
    assert len(received_wildcard) == 1
    assert received_exact[0]["reason"] == "Drawdown stop"

    # 2. Publish to different topic
    await bus.publish("orders.filled", {"order_id": "ord_123"})
    assert len(received_exact) == 1  # Not triggered
    assert len(received_wildcard) == 2  # Wildcard triggered

    # 3. Unsubscribe
    await bus.unsubscribe("risk.kill_switch", exact_handler)
    await bus.unsubscribe("*", wildcard_handler)

    await bus.publish("risk.kill_switch", {"reason": "Second event"})
    assert len(received_exact) == 1
    assert len(received_wildcard) == 2
