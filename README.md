# bip-slaskie

Daily weekday scraper pipeline for BIP legal acts in selected Silesian cities.

## Scope (current)
- City adapters scaffolded for:
  - Katowice
  - Chorzów
  - Świętochłowice
  - Siemianowice Śląskie
- Pydantic models and deterministic snapshot/diff pipeline are implemented.
- GitHub Actions weekday schedule is configured in UTC.

## Local setup
```bash
uv sync --all-groups
```

## Run locally
```bash
uv run python -m bip_scraper.cli \
  --output artifacts/current/snapshot.json \
  --previous artifacts/previous/snapshot.json \
  --report artifacts/current/report.json
```

## Quality gates
```bash
uv run ruff check .
uv run pylint src
uv run mypy src
```

Pre-commit hooks:
```bash
uv run pre-commit install
```

## Mattermost settings
All settings are read from env vars with `BIP_` prefix.

### Webhook mode
- `BIP_MATTERMOST_MODE=webhook`
- `BIP_MATTERMOST_WEBHOOK_URL=...`

### API mode
- `BIP_MATTERMOST_MODE=api`
- `BIP_MATTERMOST_API_URL=...`
- `BIP_MATTERMOST_TOKEN=...`
- `BIP_MATTERMOST_CHANNEL_ID=...`

### Disabled mode
- `BIP_MATTERMOST_MODE=disabled`
