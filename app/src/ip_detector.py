from typing import Protocol

import httpx
import structlog

logger = structlog.get_logger()


class IPDetector(Protocol):
    async def get_current_ip(self) -> str: ...


class PublicIPDetector:
    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self._providers = [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
            "https://1.1.1.1/cdn-cgi/trace",
        ]

    async def get_current_ip(self) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for provider in self._providers:
                try:
                    response = await client.get(provider)
                    response.raise_for_status()
                    ip = self._parse_response(provider, response.text)
                    await logger.adebug("IP detected from provider", provider=provider, ip=ip)
                except (httpx.HTTPError, ValueError) as e:
                    await logger.awarning("IP detection failed", provider=provider, error=str(e))
                    continue
                else:
                    return ip
        msg = "Failed to detect public IP from all providers"
        raise RuntimeError(msg)

    def _parse_response(self, provider: str, text: str) -> str:
        if "cdn-cgi/trace" in provider:
            for line in text.split("\n"):
                if line.startswith("ip="):
                    return line.split("=")[1].strip()
            msg = "Could not parse IP from Cloudflare trace"
            raise ValueError(msg)
        return text.strip()
