import pytest

from app.config import DNSRecordConfig
from app.src.models import DNSRecord


@pytest.mark.asyncio
async def test_update_creates_record_when_missing(
    ip_detector_factory,
    cloudflare_client_factory,
    updater_factory,
) -> None:
    record_config = DNSRecordConfig(name="home.example.com", type="A", ttl=300, proxied=False)
    ip_detector = ip_detector_factory("1.2.3.4")
    cf_client = cloudflare_client_factory()
    updater = updater_factory(ip_detector, cf_client, [record_config])

    changed = await updater.update()

    assert changed is True
    assert cf_client.created_calls[-1]["content"] == "1.2.3.4"
    assert not cf_client.updated_calls


@pytest.mark.asyncio
async def test_update_skips_when_record_is_up_to_date(
    ip_detector_factory,
    cloudflare_client_factory,
    updater_factory,
) -> None:
    existing = DNSRecord(id="rec-1", name="home.example.com", type="A", content="1.2.3.4")
    record_config = DNSRecordConfig(name="home.example.com", type="A", ttl=120, proxied=False)
    ip_detector = ip_detector_factory("1.2.3.4")
    cf_client = cloudflare_client_factory(records={"home.example.com": existing})
    updater = updater_factory(ip_detector, cf_client, [record_config])

    changed = await updater.update()

    assert changed is False
    assert not cf_client.updated_calls
    assert not cf_client.created_calls


@pytest.mark.asyncio
async def test_update_changes_record_when_ip_differs(
    ip_detector_factory,
    cloudflare_client_factory,
    updater_factory,
) -> None:
    existing = DNSRecord(id="rec-2", name="home.example.com", type="A", content="5.6.7.8")
    record_config = DNSRecordConfig(name="home.example.com", type="A", ttl=60, proxied=True)
    ip_detector = ip_detector_factory("1.2.3.4")
    cf_client = cloudflare_client_factory(records={"home.example.com": existing})
    updater = updater_factory(ip_detector, cf_client, [record_config])

    changed = await updater.update()

    assert changed is True
    assert cf_client.updated_calls[-1]["content"] == "1.2.3.4"


@pytest.mark.asyncio
async def test_update_skips_when_ip_has_not_changed_since_last_run(
    ip_detector_factory,
    cloudflare_client_factory,
    updater_factory,
) -> None:
    record_config = DNSRecordConfig(name="home.example.com", type="A", ttl=300, proxied=False)
    ip_detector = ip_detector_factory("1.2.3.4")
    cf_client = cloudflare_client_factory()
    updater = updater_factory(ip_detector, cf_client, [record_config])

    first_run_changed = await updater.update()
    second_run_changed = await updater.update()

    assert first_run_changed is True
    assert second_run_changed is False
    assert len(cf_client.created_calls) == 1
    assert not cf_client.updated_calls


@pytest.mark.asyncio
async def test_update_handles_multiple_records(
    ip_detector_factory,
    cloudflare_client_factory,
    updater_factory,
) -> None:
    existing = DNSRecord(id="rec-10", name="home.example.com", type="A", content="9.9.9.9")
    configs = [
        DNSRecordConfig(name="home.example.com", type="A", ttl=300, proxied=False),
        DNSRecordConfig(name="vpn.example.com", type="A", ttl=120, proxied=True),
    ]
    ip_detector = ip_detector_factory("1.2.3.4")
    cf_client = cloudflare_client_factory(records={"home.example.com": existing})
    updater = updater_factory(ip_detector, cf_client, configs)

    changed = await updater.update()

    assert changed is True
    assert len(cf_client.updated_calls) == 1
    assert len(cf_client.created_calls) == 1
    assert cf_client.records["home.example.com"].content == "1.2.3.4"
    assert cf_client.records["vpn.example.com"].content == "1.2.3.4"


@pytest.mark.asyncio
async def test_update_continues_when_cloudflare_raises(
    ip_detector_factory,
    cloudflare_client_factory,
    updater_factory,
) -> None:
    configs = [
        DNSRecordConfig(name="home.example.com", type="A", ttl=300, proxied=False),
        DNSRecordConfig(name="vpn.example.com", type="A", ttl=300, proxied=False),
    ]
    ip_detector = ip_detector_factory("1.2.3.4")
    cf_client = cloudflare_client_factory()
    cf_client.raise_on_create = True
    updater = updater_factory(ip_detector, cf_client, configs)

    changed = await updater.update()

    assert changed is False
    assert not cf_client.updated_calls


@pytest.mark.asyncio
async def test_update_retries_after_failure(
    ip_detector_factory,
    cloudflare_client_factory,
    updater_factory,
) -> None:
    record_config = DNSRecordConfig(name="home.example.com", type="A", ttl=300, proxied=False)
    ip_detector = ip_detector_factory("1.2.3.4")
    cf_client = cloudflare_client_factory()
    cf_client.raise_on_create = True
    updater = updater_factory(ip_detector, cf_client, [record_config])

    await updater.update()
    cf_client.raise_on_create = False

    changed = await updater.update()

    assert changed is True
    assert cf_client.created_calls[-1]["content"] == "1.2.3.4"
