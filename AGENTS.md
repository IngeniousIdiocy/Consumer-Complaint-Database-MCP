# Repository Guidelines for Codex Agents

This project provides a local-only Model Context Protocol (MCP) server for searching the CFPB Consumer Complaint Database. The code base is small and uses Python 3.11+.

## Setup
- Install dependencies listed in `pyproject.toml` using `uv` or plain `pip`.
- The server can be launched for a smoke test with `uv run complaints.py`.

## Testing
- Always run the unit tests before committing changes:
  ```bash
  python -m unittest discover -s tests -v
  ```
- Ensure all tests pass. Add new tests when fixing bugs or adding features.

## Style
- Format Python code with [`black`](https://black.readthedocs.io/) using default settings.
- Keep the asynchronous design when extending the server and include type hints.

## Pull Requests
- Summarize the changes and reference relevant lines from the repo in the PR description.
- Mention the result of the test command in the PR body.

