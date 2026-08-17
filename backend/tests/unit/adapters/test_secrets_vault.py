"""Unit tests for Encrypted Secrets Vault."""

import pytest
from openquant.adapters.secrets.vault import FernetSecretsVault
from openquant.domain.exceptions import SecretsDecryptionError


def test_secrets_vault_encrypt_decrypt_string_roundtrip():
    """Verify string payload encryption and decryption."""
    vault = FernetSecretsVault(master_secret="test_secret_key_1234567890123456")
    plaintext = "super_secret_broker_api_token_xyz"

    ciphertext = vault.encrypt(plaintext)
    assert ciphertext != plaintext
    assert isinstance(ciphertext, str)

    decrypted = vault.decrypt(ciphertext)
    assert decrypted == plaintext


def test_secrets_vault_encrypt_decrypt_json_roundtrip():
    """Verify dictionary payload encryption and decryption."""
    vault = FernetSecretsVault(master_secret="test_secret_key_1234567890123456")
    data = {
        "api_key": "my_api_key_123",
        "api_secret": "my_api_secret_456",
        "totp_secret": "JBSWY3DPEHPK3PXP",
    }

    ciphertext = vault.encrypt_json(data)
    assert isinstance(ciphertext, str)

    decrypted = vault.decrypt_json(ciphertext)
    assert decrypted == data


def test_secrets_vault_rejects_tampered_ciphertext():
    """Verify decryption fails when ciphertext is tampered with."""
    vault = FernetSecretsVault(master_secret="test_secret_key_1234567890123456")
    ciphertext = vault.encrypt("important_payload")

    # Corrupt ciphertext string
    corrupted = ciphertext[:-5] + "AAAAA"

    with pytest.raises(SecretsDecryptionError):
        vault.decrypt(corrupted)


def test_secrets_vault_rejects_different_master_secret():
    """Verify payload encrypted with one master key cannot be decrypted with another."""
    vault_a = FernetSecretsVault(master_secret="key_alpha_12345678901234567890")
    vault_b = FernetSecretsVault(master_secret="key_beta_123456789012345678901")

    ciphertext = vault_a.encrypt("confidential_broker_secret")

    with pytest.raises(SecretsDecryptionError):
        vault_b.decrypt(ciphertext)
