# Consumer-Complaint-Database-MCP

This repository contains a local-only [MCP](https://github.com/anthropics/mcp) server for querying the U.S. Consumer Financial Protection Bureau (CFPB) Consumer Complaint Database.  The server is designed to be launched via standard input/output, making it ideal for integration with tools such as Claude Desktop.

## Files

- `complaints.py` – Main MCP server that exposes a single tool, `search_complaints`, for retrieving complaint records from the CFPB API.
- `pyproject.toml` – Minimal project metadata and dependency declarations.
- `claude_desktop_config.json` – Example configuration for launching the server from Claude Desktop.

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) or `pip` for installing dependencies

Required Python packages are listed in `pyproject.toml` and include `httpx`, `mcp[cli]`, and `python-dateutil`.

## Setup

Install dependencies with `uv`:

```bash
uv pip install -r pyproject.toml
```

Or with plain `pip`:

```bash
pip install -r pyproject.toml
```

## Running

To launch the server directly from the command line for a smoke test:

```bash
uv run complaints.py
```

The server runs over stdio only and waits for requests from an MCP-aware client (e.g., Claude Desktop).

## Running tests

Execute the unit tests using Python's unittest discovery. From the repository
root, run:

```bash
python -m unittest discover -s tests -v
```

This requires the dependencies listed in `pyproject.toml` to be installed.

## Claude Desktop Configuration

The `claude_desktop_config.json` file includes an example entry pointing to the `complaints.py` script. Replace `INSERTPATH` with the path to this repository on your machine and import the configuration into Claude Desktop.


## References

- [CFPB Consumer Complaint Database API documentation](https://cfpb.github.io/ccdb5-api/documentation/) – underlying API used by this MCP server.
- [Model Context Protocol quickstart tutorial](https://modelcontextprotocol.io/quickstart/server) – tutorial that helped build this example.

![MCP usage in Claude](https://raw.githubusercontent.com/IngeniousIdiocy/Consumer-Complaint-Database-MCP/main/banking_complaint_mcp_usage.png)
