from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

import pytest

from app.config import DNSRecordConfig
from app.src.cloudflare_client import CloudflareClient
from app.src.dns_updater import DNSUpdater
from app.src.models import DNSRecord


class _FakeIPDetector:
    def __init__(self, ip: str) -> None:
        self._ip = ip

    def set_ip(self, ip: str) -> None:
        self._ip = ip

    async def get_current_ip(self) -> str:
        return self._ip


class _FakeCloudflareClient:
    def __init__(self, records: dict[str, DNSRecord] | None = None) -> None:
        self.records: dict[str, DNSRecord] = records or {}
        self.created_calls: list[dict[str, str]] = []
        self.updated_calls: list[dict[str, str]] = []
        self.raise_on_create = False
        self.raise_on_update = False

    async def get_dns_record(self, name: str) -> DNSRecord | None:
        return self.records.get(name)

    async def create_dns_record(
        self,
        *,
        record_name: str,
        content: str,
        ttl: int,
        proxied: bool,
    ) -> DNSRecord:
        if self.raise_on_create:
            msg = "create failed"
            raise RuntimeError(msg)
        payload = {
            "name": record_name,
            "content": content,
            "ttl": str(ttl),
            "proxied": str(proxied),
        }
        self.created_calls.append(payload)
        record = DNSRecord(id=f"{record_name}-id", name=record_name, content=content)
        self.records[record_name] = record
        return record

    async def update_dns_record(
        self,
        *,
        record_id: str,
        record_name: str,
        content: str,
        ttl: int,
        proxied: bool,
    ) -> DNSRecord:
        if self.raise_on_update:
            msg = "update failed"
            raise RuntimeError(msg)
        payload = {
            "id": record_id,
            "name": record_name,
            "content": content,
            "ttl": str(ttl),
            "proxied": str(proxied),
        }
        self.updated_calls.append(payload)
        record = DNSRecord(id=record_id, name=record_name, content=content)
        self.records[record_name] = record
        return record


class _FakeRecordsResource:
    def __init__(self) -> None:
        self.list_result: list[Any] = []
        self.create_result: Any = None
        self.update_result: Any = None
        self.last_kwargs: dict[str, Any] | None = None

    def list(self, **kwargs: Any) -> SimpleNamespace:
        self.last_kwargs = kwargs
        return SimpleNamespace(result=self.list_result)

    def create(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        return self.create_result

    def update(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        return self.update_result


class _FakeCloudflareSDK:
    def __init__(self, records: _FakeRecordsResource) -> None:
        self.dns = SimpleNamespace(records=records)


@pytest.fixture
def ip_detector_factory() -> Callable[[str], _FakeIPDetector]:
    def factory(ip: str = "1.1.1.1") -> _FakeIPDetector:
        return _FakeIPDetector(ip)

    return factory


@pytest.fixture
def cloudflare_client_factory() -> Callable[[dict[str, DNSRecord] | None], _FakeCloudflareClient]:
    def factory(records: dict[str, DNSRecord] | None = None) -> _FakeCloudflareClient:
        return _FakeCloudflareClient(records=records)

    return factory


@pytest.fixture
def updater_factory() -> Callable[
    [_FakeIPDetector, _FakeCloudflareClient, list[DNSRecordConfig]], DNSUpdater
]:
    def factory(
        ip_detector: _FakeIPDetector,
        cloudflare_client: _FakeCloudflareClient,
        record_configs: list[DNSRecordConfig],
    ) -> DNSUpdater:
        config = SimpleNamespace(update_interval=60)
        return DNSUpdater(config, ip_detector, cloudflare_client, record_configs)

    return factory


@pytest.fixture
def cloudflare_client_stub(monkeypatch: pytest.MonkeyPatch) -> tuple[CloudflareClient, _FakeRecordsResource]:
    records = _FakeRecordsResource()

    def factory(api_token: str) -> _FakeCloudflareSDK:
        return _FakeCloudflareSDK(records)

    monkeypatch.setattr("app.src.cloudflare_client.Cloudflare", factory)
    client = CloudflareClient(api_token="token", zone_id="zone")
    return client, records


__all__ = [
    "_FakeIPDetector",
    "_FakeCloudflareClient",
    "_FakeRecordsResource",
]

