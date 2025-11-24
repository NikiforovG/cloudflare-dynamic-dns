from types import SimpleNamespace

import pytest

from app.src.models import DNSRecord


@pytest.mark.asyncio
async def test_get_dns_record_returns_converted_record(cloudflare_client_stub) -> None:
    client, records = cloudflare_client_stub
    raw = SimpleNamespace(id="rec-1", name="home.example.com", type="A", content="1.2.3.4")
    records.list_result = [raw]

    record = await client.get_dns_record("home.example.com", "A")

    assert isinstance(record, DNSRecord)
    assert record and record.content == "1.2.3.4"
    assert records.last_kwargs["zone_id"] == "zone"


@pytest.mark.asyncio
async def test_get_dns_record_returns_none_when_missing(cloudflare_client_stub) -> None:
    client, records = cloudflare_client_stub
    records.list_result = []

    record = await client.get_dns_record("missing.example.com", "A")

    assert record is None


@pytest.mark.asyncio
async def test_create_dns_record_raises_when_response_empty(cloudflare_client_stub) -> None:
    client, records = cloudflare_client_stub
    records.create_result = None

    with pytest.raises(RuntimeError):
        await client.create_dns_record("home.example.com", "A", "1.2.3.4")


@pytest.mark.asyncio
async def test_update_dns_record_returns_converted(cloudflare_client_stub) -> None:
    client, records = cloudflare_client_stub
    raw = SimpleNamespace(id="rec-1", name="home.example.com", type="A", content="5.6.7.8")
    records.update_result = raw

    result = await client.update_dns_record(
        record_id="rec-1",
        record_name="home.example.com",
        record_type="A",
        content="5.6.7.8",
        ttl=300,
        proxied=False,
    )

    assert result.id == "rec-1"
    assert result.content == "5.6.7.8"

