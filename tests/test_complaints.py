import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Provide dummy mcp module hierarchy
if 'mcp' not in sys.modules:
    mcp_mod = types.ModuleType('mcp')
    server_mod = types.ModuleType('mcp.server')
    fastmcp_mod = types.ModuleType('mcp.server.fastmcp')
    exceptions_mod = types.ModuleType('mcp.server.fastmcp.exceptions')

    class DummyFastMCP:
        def __init__(self, *args, **kwargs):
            pass
        def tool(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def run(self, *args, **kwargs):
            pass
    fastmcp_mod.FastMCP = DummyFastMCP
    class ToolError(Exception):
        pass
    exceptions_mod.ToolError = ToolError

    server_mod.fastmcp = fastmcp_mod
    mcp_mod.server = server_mod

    sys.modules['mcp'] = mcp_mod
    sys.modules['mcp.server'] = server_mod
    sys.modules['mcp.server.fastmcp'] = fastmcp_mod
    sys.modules['mcp.server.fastmcp.exceptions'] = exceptions_mod

# Provide dummy httpx module
if 'httpx' not in sys.modules:
    dummy_httpx = types.ModuleType('httpx')
    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, *args, **kwargs):
            class Resp:
                status_code = 200
                def json(self):
                    return {}
                text = ''
            return Resp()
    dummy_httpx.AsyncClient = DummyAsyncClient
    sys.modules['httpx'] = dummy_httpx

# Provide dummy dateutil.parser module
if 'dateutil' not in sys.modules:
    dummy_dateutil = types.ModuleType('dateutil')
    parser_mod = types.ModuleType('dateutil.parser')
    def parse(value):
        import datetime
        return datetime.datetime.fromisoformat(value)
    parser_mod.parse = parse
    dummy_dateutil.parser = parser_mod
    sys.modules['dateutil'] = dummy_dateutil
    sys.modules['dateutil.parser'] = parser_mod

from complaints import search_complaints, Complaint

TEST_DIR = Path(__file__).parent

class SearchComplaintsTest(unittest.IsolatedAsyncioTestCase):
    async def test_search_complaints(self):
        with open(TEST_DIR / 'data' / 'test_query.json') as f:
            query = json.load(f)
        with open(TEST_DIR / 'data' / 'test_query_response.json') as f:
            raw_results = json.load(f)
        expected = [Complaint.from_json(item) for item in raw_results]

        mock_fetch = AsyncMock(return_value=expected)
        with patch('complaints._fetch_cfpb', new=mock_fetch):
            results = await search_complaints(**query)
            self.assertEqual(results, expected)
            mock_fetch.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
