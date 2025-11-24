import structlog

from app.config import Config, DNSRecordConfig

from .cloudflare_client import CloudflareClient
from .ip_detector import IPDetector

logger = structlog.get_logger()


class DNSUpdater:
    def __init__(
        self,
        config: Config,
        ip_detector: IPDetector,
        cloudflare_client: CloudflareClient,
        dns_records: list[DNSRecordConfig],
    ) -> None:
        self._config = config
        self._ip_detector = ip_detector
        self._cloudflare_client = cloudflare_client
        self._dns_records = dns_records
        self._last_ip: str | None = None

    async def update(self) -> bool:
        current_ip = await self._ip_detector.get_current_ip()
        await logger.ainfo("Current IP detected", ip=current_ip)

        if current_ip == self._last_ip:
            await logger.ainfo("IP unchanged, skipping update")
            return False

        updated = False
        had_errors = False

        for record_config in self._dns_records:
            try:
                updated |= await self._update_record(current_ip, record_config)
            except Exception:  # noqa: BLE001
                await logger.aexception(
                    "Failed to update record",
                    record_name=record_config.name,
                )
                had_errors = True

        self._last_ip = None if had_errors else current_ip
        return updated

    async def _update_record(self, current_ip: str, record_config: DNSRecordConfig) -> bool:
        existing_record = await self._cloudflare_client.get_dns_record(
            record_config.name,
            record_config.type,
        )

        if existing_record:
            if existing_record.content == current_ip:
                await logger.ainfo("Record already up to date", record_name=record_config.name, ip=current_ip)
                return False

            await self._cloudflare_client.update_dns_record(
                record_id=existing_record.id,
                record_name=record_config.name,
                record_type=record_config.type,
                content=current_ip,
                ttl=record_config.ttl,
                proxied=record_config.proxied,
            )
            await logger.ainfo(
                "Record updated",
                record_name=record_config.name,
                old_ip=existing_record.content,
                new_ip=current_ip,
            )
        else:
            await self._cloudflare_client.create_dns_record(
                record_name=record_config.name,
                record_type=record_config.type,
                content=current_ip,
                ttl=record_config.ttl,
                proxied=record_config.proxied,
            )
            await logger.ainfo("Record created", record_name=record_config.name, ip=current_ip)

        return True
