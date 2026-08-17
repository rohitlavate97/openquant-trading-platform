"""Application service for Secure Broker Credentials Vault."""

import uuid
from typing import Any
from openquant.domain.models.auth import BrokerCredentialVaultItem
from openquant.domain.ports.secrets_manager import ISecretsManager
from openquant.domain.ports.user_repository import ICredentialVaultRepository
from openquant.adapters.secrets.vault import secrets_vault as default_secrets_vault
from openquant.adapters.repositories.in_memory_auth_repo import credential_vault_repository as default_vault_repo


class SecretsService:
    """Manages encrypted storage and retrieval of sensitive broker credentials."""

    def __init__(
        self,
        vault_repo: ICredentialVaultRepository = default_vault_repo,
        secrets_manager: ISecretsManager = default_secrets_vault,
    ) -> None:
        self._vault_repo = vault_repo
        self._secrets_manager = secrets_manager

    @staticmethod
    def _mask_value(val: str) -> str:
        """Create a safe masked string for display e.g. ••••••••1234."""
        if len(val) <= 4:
            return "••••"
        return f"{'•' * (len(val) - 4)}{val[-4:]}"

    async def store_broker_credentials(
        self,
        user_id: str,
        broker_id: str,
        account_id: str,
        credentials: dict[str, str],
    ) -> BrokerCredentialVaultItem:
        """Encrypt credentials dictionary and store in vault."""
        encrypted_payload = self._secrets_manager.encrypt_json(credentials)

        item = BrokerCredentialVaultItem(
            credential_id=f"cred_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            broker_id=broker_id,
            account_id=account_id,
            encrypted_payload=encrypted_payload,
            key_version=1,
        )
        await self._vault_repo.save_credential(item)
        return item

    async def get_decrypted_credentials(
        self,
        user_id: str,
        broker_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve and decrypt credentials. Only invoked by authenticated adapter execution engine."""
        item = await self._vault_repo.get_credential(user_id, broker_id)
        if not item:
            return None
        return self._secrets_manager.decrypt_json(item.encrypted_payload)

    async def list_masked_credentials(self, user_id: str) -> list[dict[str, Any]]:
        """List stored credentials with masked values for UI display."""
        items = await self._vault_repo.list_user_credentials(user_id)
        results = []
        for item in items:
            decrypted = self._secrets_manager.decrypt_json(item.encrypted_payload)
            masked_fields = {
                k: self._mask_value(v) if isinstance(v, str) else "••••"
                for k, v in decrypted.items()
            }
            results.append({
                "credential_id": item.credential_id,
                "broker_id": item.broker_id,
                "account_id": item.account_id,
                "masked_fields": masked_fields,
                "key_version": item.key_version,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            })
        return results

    async def delete_credential(self, user_id: str, broker_id: str) -> bool:
        """Revoke and delete a stored broker credential."""
        return await self._vault_repo.delete_credential(user_id, broker_id)


# Global singleton instance
secrets_service = SecretsService()
