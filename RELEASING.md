# Releasing saverapi-client

Source of the `saverapi-client` package on PyPI.

```bash
python -m venv .venv && . .venv/bin/activate
pip install build twine pytest requests httpx
pytest -q tests                       # must pass
# bump saverapi/_version.py and the Changelog in README.md
rm -rf dist && python -m build
twine check dist/*
TWINE_USERNAME=__token__ TWINE_PASSWORD=<pypi token scoped to saverapi-client> twine upload dist/*
```

Never commit the token. Endpoints and parameter names must match the live
catalog (`/api/apis`, active endpoints only — remove methods for retired ones in a major release); note that `/youtube-api` spells its quality parameter `farmat`.
