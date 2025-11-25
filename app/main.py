import asyncio
import sys
from typing import NoReturn

import structlog

from app.config import Config
from app.src.cloudflare_client import CloudflareClient
from app.src.dns_updater import DNSUpdater
from app.src.ip_detector import PublicIPDetector

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()


async def run_daemon(config: Config) -> NoReturn:
    dns_records = config.load_dns_records()

    ip_detector = PublicIPDetector()
    cloudflare_client = CloudflareClient(config.cloudflare_api_token, config.cloudflare_zone_id)
    updater = DNSUpdater(config, ip_detector, cloudflare_client, dns_records)

    await logger.ainfo(
        "Daemon started",
        interval=config.update_interval,
        records=[r.name for r in dns_records],
        config_file=config.records_config_path,
    )

    while True:
        try:
            await updater.update()
        except Exception:  # noqa: BLE001
            await logger.aexception("Update failed")

        await asyncio.sleep(config.update_interval)


def main() -> None:
    try:
        config = Config()  # type: ignore[call-arg]
    except Exception:
        logger.exception("Failed to load configuration")
        sys.exit(1)

    try:
        asyncio.run(run_daemon(config))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
