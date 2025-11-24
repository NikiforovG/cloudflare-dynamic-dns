import json
from pathlib import Path

import structlog
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from app.src.models import RecordType

logger = structlog.get_logger()


class DNSRecordConfig(BaseModel):
    name: str = Field(..., description="DNS record name")
    type: RecordType = Field(default="A", description="DNS record type")
    proxied: bool = Field(default=False, description="Whether to proxy through Cloudflare")
    ttl: int = Field(default=300, description="DNS record TTL in seconds")


class DNSRecordsConfig(BaseModel):
    records: list[DNSRecordConfig] = Field(..., description="List of DNS records to manage")


class Config(BaseSettings):
    cloudflare_api_token: str = Field(..., description="Cloudflare API token")
    cloudflare_zone_id: str = Field(..., description="Cloudflare Zone ID")
    records_config_path: str = Field(
        default="./config/records.json",
        description="Path to DNS records configuration file (JSON)",
    )
    update_interval: int = Field(default=300, description="Update check interval in seconds")

    def load_dns_records(self) -> list[DNSRecordConfig]:
        try:
            config_path = Path(self.records_config_path)
            with config_path.open() as f:
                data = json.load(f)
            records_config = DNSRecordsConfig(**data)
        except Exception:
            logger.exception("Failed to load DNS records")
            raise
        else:
            return records_config.records
