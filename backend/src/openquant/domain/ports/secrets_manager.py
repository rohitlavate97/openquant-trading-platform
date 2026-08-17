"""Hexagonal Port: Abstract Secrets Manager Interface.

Defines the contract for cryptographic encryption and decryption of broker API keys,
passwords, and webhook secrets at rest.
"""

from abc import ABC, abstractmethod
from typing import Any


class ISecretsManager(ABC):
    """Abstract interface for authenticated encryption and decryption of sensitive secrets."""

    @abstractmethod
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string into an authenticated ciphertext."""

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt authenticated ciphertext back to plaintext string."""

    @abstractmethod
    def encrypt_json(self, data: dict[str, Any]) -> str:
        """Serialize and encrypt a dictionary payload into an authenticated ciphertext."""

    @abstractmethod
    def decrypt_json(self, ciphertext: str) -> dict[str, Any]:
        """Decrypt and deserialize ciphertext back to dictionary payload."""
