"""Domain exceptions expressing core business rule violations and capital-safety guards."""


class OpenQuantDomainError(Exception):
    """Base exception for all domain-specific errors in OpenQuant."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class CapitalSafetyViolationError(OpenQuantDomainError):
    """Raised when an action violates an essential capital preservation invariant."""


class KillSwitchActiveError(CapitalSafetyViolationError):
    """Raised when an order placement or modification is attempted while Kill Switch is active."""


class RiskLimitBreachedError(CapitalSafetyViolationError):
    """Raised when a pre-trade risk rule (daily loss, max drawdown, exposure) is breached."""


class PromotionGateViolationError(CapitalSafetyViolationError):
    """Raised when a strategy attempts to bypass or execute in an unauthorized promotion stage."""


class BrokerAdapterUncertifiedError(CapitalSafetyViolationError):
    """Raised when attempting live trading with a broker adapter that hasn't passed certification."""


class IdempotencyConflictError(OpenQuantDomainError):
    """Raised when an order submission with an identical idempotency key is already processed."""


class StaleMarketDataError(CapitalSafetyViolationError):
    """Raised when a trading decision or order calculation relies on market data exceeding staleness threshold."""


class SandboxSecurityViolationError(OpenQuantDomainError):
    """Raised when strategy code fails AST static analysis or attempts prohibited system operations."""


class SandboxResourceExceededError(OpenQuantDomainError):
    """Raised when a strategy exceeds its allocated CPU, memory, or wall-clock time budget."""


# ------------------------------------------------------------------------------
# Authentication, RBAC & Secrets Management Domain Exceptions
# ------------------------------------------------------------------------------

class AuthenticationError(OpenQuantDomainError):
    """Raised when user credentials or token verification fails."""


class PermissionDeniedError(OpenQuantDomainError):
    """Raised when an authenticated actor lacks required RBAC permissions."""


class InvalidTokenError(AuthenticationError):
    """Raised when a JWT token is expired, malformed, or has an invalid signature."""


class UserAlreadyExistsError(OpenQuantDomainError):
    """Raised when attempting to register a user with an already registered email."""


class SecretsDecryptionError(OpenQuantDomainError):
    """Raised when ciphertext cannot be decrypted due to key mismatch or corrupted payload."""


class APIKeyRevokedError(AuthenticationError):
    """Raised when an API key has been revoked or expired."""


class BrokerAdapterNotFoundError(OpenQuantDomainError):
    """Raised when an operation requests a non-existent or unregistered broker adapter."""


class BrokerConnectionError(OpenQuantDomainError):
    """Raised when broker handshake, authentication, or network session fails."""


class OrderPlacementError(OpenQuantDomainError):
    """Raised when an order cannot be placed or modified by the broker adapter."""


class OrderCancellationError(OpenQuantDomainError):
    """Raised when an order cannot be cancelled by the broker adapter or is invalid."""


