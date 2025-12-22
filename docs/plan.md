---
title: Project Plan
---

# 🗺️ Project Plan / Roadmap

This document tracks near-term maintenance work and longer-term improvements for DroidMind.

## ✅ Maintenance Baseline

- Keep dependencies current via `uv lock --upgrade` + CI green.
- Support **Python 3.13** (Python 3.14 support depends on transitive ecosystem readiness).
- Ensure Docker builds are reproducible using `uv.lock`.

## 🔜 Next Up

- Replace usage of private MCP internals (e.g. `mcp._mcp_server`) with public APIs when available.
- Add a lightweight “smoke test” CI job that boots `droidmind --transport sse` and performs a basic MCP handshake.
- Clarify packaging and installation paths (source/dev vs `uvx` usage) and keep docs consistent.

## 💡 Nice-to-Haves

- Add optional dependency sets (e.g. minimal `stdio` vs `sse`) once imports are fully modular.
- Add integration tests against a real Android emulator in CI (opt-in / nightly).

