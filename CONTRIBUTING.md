# Contributing to HA Bin Collection

Install dependencies with `uv sync`. Run the complete validation suite before sharing a change:

```sh
uv run ruff check && uv run ruff format --check && uv run ty check && uv run pytest
```

Provider additions should implement the provider contract, return normalized collection and notice records, and add aliases where a collector uses a different name for Rest, Papier, GFT, or PMD. Add mocked provider responses and keep English/Dutch translations and README examples in sync.

## Contribution workflow

1. Fork [hunter-nl/HA-Bin-Collection](https://github.com/hunter-nl/HA-Bin-Collection).
2. Create a `feature/` or `fix/` branch from `main`.
3. Keep user-facing behavior, translations, documentation, and tests in sync.
4. Commit with a clear Conventional Commit message and open a pull request against `main`.

## License

By contributing, you agree that your contributions are licensed under AGPL-3.0-only.

## Funding

If you find this project useful, consider supporting its development:

<a href="https://www.buymeacoffee.com/hunter.nl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>
