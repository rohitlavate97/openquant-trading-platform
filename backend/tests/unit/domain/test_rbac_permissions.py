"""Unit tests for Role-Based Access Control and Permission Resolution."""

from openquant.domain.models.auth import Permission, User, UserRole


def test_super_admin_has_all_permissions():
    """Verify SUPER_ADMIN role holds full system, kill switch, and live trading permissions."""
    user = User(
        user_id="usr_super",
        email="super@openquant.org",
        hashed_password="hash",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
    )
    assert user.has_permission(Permission.SYSTEM_ADMIN) is True
    assert user.has_permission(Permission.KILL_SWITCH_TRIGGER) is True
    assert user.has_permission(Permission.LIVE_TRADING_ENABLE) is True
    assert user.has_permission(Permission.STRATEGY_APPROVE) is True
    assert user.has_permission(Permission.BROKER_MANAGE) is True


def test_viewer_has_only_read_permission():
    """Verify VIEWER role cannot trigger kill switch, manage brokers, or enable live trading."""
    user = User(
        user_id="usr_viewer",
        email="viewer@openquant.org",
        hashed_password="hash",
        full_name="Auditor Viewer",
        role=UserRole.VIEWER,
    )
    assert user.has_permission(Permission.READ_ONLY) is True
    assert user.has_permission(Permission.KILL_SWITCH_TRIGGER) is False
    assert user.has_permission(Permission.LIVE_TRADING_ENABLE) is False
    assert user.has_permission(Permission.BROKER_MANAGE) is False
    assert user.has_permission(Permission.ORDER_MANAGE) is False


def test_trader_and_quant_dev_permissions():
    """Verify distinct capabilities between Quant Developer and Trader."""
    quant = User(
        user_id="usr_quant",
        email="quant@openquant.org",
        hashed_password="hash",
        full_name="Quant Dev",
        role=UserRole.QUANT_DEVELOPER,
    )
    trader = User(
        user_id="usr_trader",
        email="trader@openquant.org",
        hashed_password="hash",
        full_name="Desk Trader",
        role=UserRole.TRADER,
    )

    # Quant developer can create strategies
    assert quant.has_permission(Permission.STRATEGY_CREATE) is True
    assert quant.has_permission(Permission.KILL_SWITCH_TRIGGER) is True
    assert quant.has_permission(Permission.STRATEGY_APPROVE) is False

    # Trader has order management and kill switch
    assert trader.has_permission(Permission.ORDER_MANAGE) is True
    assert trader.has_permission(Permission.KILL_SWITCH_TRIGGER) is True
    assert trader.has_permission(Permission.STRATEGY_CREATE) is False
