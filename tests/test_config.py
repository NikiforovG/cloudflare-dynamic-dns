import json
from pathlib import Path

import pytest

from app.config import Config


def make_config(tmp_path: Path, *, records: dict | None = None) -> Config:
    config_path = tmp_path / "records.json"
    data = records or {
        "records": [
            {"name": "home.example.com", "type": "A", "ttl": 300, "proxied": False},
            {"name": "vpn.example.com", "type": "AAAA", "ttl": 60, "proxied": True},
        ]
    }
    config_path.write_text(json.dumps(data))
    return Config(
        cloudflare_api_token="token",
        cloudflare_zone_id="zone",
        records_config_path=str(config_path),
        update_interval=120,
    )


def test_load_dns_records_success(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    records = config.load_dns_records()

    assert len(records) == 2
    assert records[0].name == "home.example.com"
    assert records[1].type == "AAAA"


def test_load_dns_records_raises_for_missing_file(tmp_path: Path) -> None:
    config = Config(
        cloudflare_api_token="token",
        cloudflare_zone_id="zone",
        records_config_path=str(tmp_path / "missing.json"),
        update_interval=120,
    )

    with pytest.raises(FileNotFoundError):
        config.load_dns_records()


def test_load_dns_records_invalid_json(tmp_path: Path) -> None:
    config_path = tmp_path / "records.json"
    config_path.write_text("not-json")
    config = Config(
        cloudflare_api_token="token",
        cloudflare_zone_id="zone",
        records_config_path=str(config_path),
        update_interval=120,
    )

    with pytest.raises(json.JSONDecodeError):
        config.load_dns_records()

