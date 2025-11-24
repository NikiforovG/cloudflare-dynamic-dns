## Cloudflare Dynamic DNS

![CI](https://github.com/nikiforovg/cloudflare-dynamic-dns/actions/workflows/ci.yml/badge.svg?branch=main)
[![Coverage](https://codecov.io/gh/nikiforovg/cloudflare-dynamic-dns/branch/main/graph/badge.svg)](https://codecov.io/gh/nikiforovg/cloudflare-dynamic-dns)
![Version](https://img.shields.io/github/v/tag/nikiforovg/cloudflare-dynamic-dns?label=version)

Docker image: [`nikiforovgv/cloudflare-ddns`](https://hub.docker.com/r/nikiforovgv/cloudflare-ddns)

Keeps one or more Cloudflare DNS records synced with your current public IP. The daemon periodically checks your IP, compares it with the records you configured, and creates or updates Cloudflare entries when needed.

### Configuration
- `CLOUDFLARE_API_TOKEN` – API token with DNS edit permissions for the zone.
- `CLOUDFLARE_ZONE_ID` – Cloudflare zone identifier.
- `RECORDS_CONFIG_PATH` – optional path to the DNS records file (defaults to `./config/records.json`).
- `UPDATE_INTERVAL` – optional poll interval in seconds (defaults to `300`).

The records file is JSON shaped like:
```json
{
  "records": [
    {"name": "home.example.com", "type": "A", "ttl": 300, "proxied": false},
    {"name": "vpn.example.com", "type": "AAAA", "ttl": 120, "proxied": true}
  ]
}
```

### Local run with Poetry
```sh
poetry install
poetry run cloudflare-ddns
```

### Docker usage
The container expects your config file to be mounted into `/app/config`. Example Compose file:
```yaml
services:
  ddns:
    image: nikiforovgv/cloudflare-ddns:latest
    build: .
    restart: unless-stopped
    environment:
      CLOUDFLARE_API_TOKEN: ${CLOUDFLARE_API_TOKEN}
      CLOUDFLARE_ZONE_ID: ${CLOUDFLARE_ZONE_ID}
      RECORDS_CONFIG_PATH: /app/config/records.json
      UPDATE_INTERVAL: 300
    volumes:
      - ./config:/app/config:ro
```
Create `config/records.json` alongside `docker-compose.yml`, then run:
```sh
docker compose up -d --build
```
