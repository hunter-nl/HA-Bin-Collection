# AGENTS.md

## Project Overview

This is the Bin Collection integration for Home Assistant.

## Setup Commands

- Install dependencies: `uv sync`
- Run all checks (lint, format, type, test): `uv run ruff check && uv run ruff format --check && uv run ty check && uv run pytest`
- Run tests: `uv run pytest`
- Run linter: `uv run ruff check`
- Run type checker: `uv run ty check`
- Format code: `uv run ruff format`

## MCP servers

- Use GitHub MCP tools for managing repositories, issues, and pull requests
- Use Context7 MCP when you need library/API documentation, code generation, setup, or configuration steps

## General rules

- Before making implementation changes, create and switch to a dedicated branch using an appropriate prefix such as `fix/`, `feature/`, or `docs/`. Never make or commit implementation changes directly on `main`; prepare them for review through a pull request.
- Always ask if you are unsure what to do or if the potential impact of a change is large
- Always use Context7 MCP when you need library/API documentation, code generation, setup, or configuration
 steps without the user explicitly asking
- Comments: Use sparingly, explain WHY not WHAT
- Mirror patterns from existing integration modules under `custom_components/ha_bin_collection` and tests under `tests`.
- Prioritize maintainability, testability, and performance while matching existing simplicity. Follow logging, typing, and retry patterns already used.

## Architecture & Module Boundaries

- `config_flow.py`: Defines interval and maintain the labels list.
- `__init__.py`: Integration setup, device registration, migration logic, coordinator instantiation.
