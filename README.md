## Cloudflare Dynamic DNS

![CI](https://github.com/nikiforovg/cloudflare-dynamic-dns/actions/workflows/ci.yml/badge.svg?branch=main)
[![Coverage](https://codecov.io/gh/nikiforovg/cloudflare-dynamic-dns/branch/main/graph/badge.svg)](https://codecov.io/gh/nikiforovg/cloudflare-dynamic-dns)
![Version](https://img.shields.io/github/v/tag/nikiforovg/cloudflare-dynamic-dns?label=version)

Docker image: [`nikiforovgv/cloudflare-ddns`](https://hub.docker.com/r/nikiforovgv/cloudflare-ddns)

Keeps one or more Cloudflare DNS records synced with your current public IP. The daemon periodically checks your IP, compares it with the records you configured, and creates or updates Cloudflare entries when needed.

Only IPv4 `A` records are supported; all entries will receive the detected public IPv4 address.

### Configuration
- `CLOUDFLARE_API_TOKEN` – API token with DNS edit permissions for the zone.
- `CLOUDFLARE_ZONE_ID` – Cloudflare zone identifier.
- `RECORDS_CONFIG_PATH` – optional path to the DNS records file (defaults to `./config/records.json`).
- `UPDATE_INTERVAL` – optional poll interval in seconds (defaults to `300`).

The records file is JSON shaped like:
```json
{
  "records": [
    {"name": "home.example.com", "ttl": 300, "proxied": false},
    {"name": "vpn.example.com", "ttl": 120, "proxied": true}
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

### Releases

Releases use annotated Git tags such as `v0.1.2`. Only stable `vX.Y.Z` tags
publish Docker images; branch pushes and pull requests run checks only.

Start from a clean, up-to-date `main`. Run the checks before preparing a release:

```sh
poetry run make format
poetry run make check
poetry run make test
```

After review, bump the version and push the release in one command:

```sh
poetry run make release
```

The default is a patch release. Use `poetry run make release PART=minor` or
`PART=major` for a larger increment. The target requires `main`, runs formatting,
and uses bumpversion to update `.bumpversion.cfg`, `pyproject.toml`, and
`app/__init__.py` together, commit the changes, and create the matching annotated
tag (for example, `v0.1.2`). It then pushes `main` and that tag atomically.

To prepare changes for staged review before committing, use
`poetry run bumpversion --no-commit --no-tag patch` instead; after the reviewed
commit, create its tag with `git tag -a "v$(poetry version --short)" -m "Release $(poetry version --short)"`.

For the staged-review flow, or to retry a failed push without bumping again:

```sh
git push --atomic origin main "refs/tags/v$(poetry version --short)"
```

CI validates the tag against the package and application versions, then runs
linting and tests before publishing `nikiforovgv/cloudflare-ddns:0.1.2`, `:latest`,
and the commit-SHA tag.
`latest` follows the last published release. Prerelease tags are not supported.
