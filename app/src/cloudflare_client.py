from typing import TYPE_CHECKING, Literal

import structlog
from cloudflare import Cloudflare
from cloudflare.types.dns import RecordResponse, record_list_params

if TYPE_CHECKING:
    from cloudflare.pagination import SyncV4PagePaginationArray

from app.src.models import DNSRecord

logger = structlog.get_logger()


_RECORD_TYPE: Literal["A"] = "A"


class CloudflareClient:
    def __init__(self, api_token: str, zone_id: str) -> None:
        self._client = Cloudflare(api_token=api_token)
        self._zone_id = zone_id

    async def get_dns_record(self, record_name: str) -> DNSRecord | None:
        await logger.adebug("Fetching DNS record", record_name=record_name, record_type=_RECORD_TYPE)
        name_filter: record_list_params.Name = {"exact": record_name}
        records: SyncV4PagePaginationArray[RecordResponse] = self._client.dns.records.list(
            zone_id=self._zone_id,
            name=name_filter,
            type=_RECORD_TYPE,
        )

        if not records.result:
            return None

        return self._to_dns_record(records.result[0])

    async def create_dns_record(
        self,
        record_name: str,
        content: str,
        *,
        ttl: int = 300,
        proxied: bool = False,
    ) -> DNSRecord:
        await logger.adebug(
            "Creating DNS record",
            record_name=record_name,
            record_type=_RECORD_TYPE,
            content=content,
        )
        raw_record = self._client.dns.records.create(
            zone_id=self._zone_id,
            name=record_name,
            type=_RECORD_TYPE,
            content=content,
            ttl=ttl,
            proxied=proxied,
        )

        return self._to_dns_record(self._ensure_record_response(raw_record, "created", record_name))

    async def update_dns_record(
        self,
        record_id: str,
        record_name: str,
        content: str,
        *,
        ttl: int = 300,
        proxied: bool = False,
    ) -> DNSRecord:
        await logger.adebug(
            "Updating DNS record",
            record_id=record_id,
            record_name=record_name,
            content=content,
        )
        raw_record = self._client.dns.records.update(
            dns_record_id=record_id,
            zone_id=self._zone_id,
            name=record_name,
            type=_RECORD_TYPE,
            content=content,
            ttl=ttl,
            proxied=proxied,
        )

        return self._to_dns_record(self._ensure_record_response(raw_record, "updated", record_id))

    def _ensure_record_response(self, record: RecordResponse | None, action: str, identifier: str) -> RecordResponse:
        if record is None:
            msg = f"Cloudflare returned an empty response when {action} DNS record {identifier}"
            raise RuntimeError(msg)
        return record

    def _to_dns_record(self, raw_record: RecordResponse) -> DNSRecord:
        content = getattr(raw_record, "content", None)
        normalized_content = None if content is None else str(content)
        return DNSRecord(
            id=raw_record.id,
            name=raw_record.name,
            content=normalized_content,
        )
