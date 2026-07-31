# MCP Server for Cisco FMC

[![CI](https://github.com/leonbreukelman/fmc-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/leonbreukelman/fmc-mcp/actions/workflows/ci.yml)
[![CodeQL](https://github.com/leonbreukelman/fmc-mcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/leonbreukelman/fmc-mcp/actions/workflows/codeql.yml)

A read-only Model Context Protocol (MCP) server for Cisco Firepower Management Center (FMC) 7.4.x.

This server allows LLMs like Claude to query your firewall configuration, search for network objects, and check deployment status—all through natural language.

## Features

- **Read-Only Access**: Safe exploration of FMC configuration without modification risk
- **Rate Limiting**: Built-in token bucket rate limiter (120 req/min, 10 concurrent connections)
- **Automatic Token Refresh**: Handles FMC's 30-minute token expiration and 3-refresh limit
- **Transparent Pagination**: Automatically fetches all pages from large datasets
- **Explicit Unknown States**: Permission denial and unknown devices never report false success

### MCP Resources

| Resource | Description |
|----------|-------------|
| `fmc://system/info` | FMC server version and system information |
| `fmc://devices/list` | List of all managed firewall devices |
| `fmc://objects/network` | All network objects (IPs, subnets) |
| `fmc://deployment/status` | Devices with pending changes |

### MCP Tools

| Tool | Description |
|------|-------------|
| `search_object_by_ip` | Find network objects containing a specific IP |
| `get_deployment_status` | Check if devices are in sync |

## Installation

### Prerequisites

- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Access to a Cisco FMC 7.4.x instance

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/leonbreukelman/fmc-mcp.git
cd fmc-mcp

# Install dependencies
uv sync
```

### Using pip

```bash
pip install -e .
```

## Configuration

1. Copy the example configuration:

```bash
cp .env.example .env
```

2. Edit `.env` with your FMC credentials:

```env
FMC_HOST=fmc.example.com
FMC_USERNAME=api_user
FMC_PASSWORD=your_password_here
```

### Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FMC_HOST` | Yes | - | FMC hostname or IP |
| `FMC_USERNAME` | Yes | - | API username |
| `FMC_PASSWORD` | Yes | - | API password |
| `FMC_VERIFY_SSL` | No | `false` | SSL certificate verification; set `true` in production |
| `FMC_DOMAIN_UUID` | No | auto | Domain UUID (auto-discovered) |
| `FMC_TIMEOUT` | No | `60` | Positive request timeout in seconds |
| `FMC_RATE_LIMIT` | No | `120` | Positive maximum FMC requests per minute |
| `FMC_MAX_CONNECTIONS` | No | `10` | Positive maximum concurrent FMC requests |
| `MCP_TRANSPORT` | No | `stdio` | Transport mode: `stdio` or `http` |
| `MCP_HOST` | No | `127.0.0.1` | HTTP server host (HTTP mode only) |
| `MCP_PORT` | No | `8080` | HTTP server port (HTTP mode only) |

## Usage

### Running the Server

#### stdio Mode (Default - for Claude Desktop)

```bash
# Using uv
uv run python -m fmc_mcp

# Or using the CLI entry point
uv run mcp-server-fmc
```

#### HTTP/SSE Mode (for Integration Testing)

HTTP/SSE mode enables multiple client connections and integration testing scenarios:

```bash
# Set environment variable for HTTP mode
export MCP_TRANSPORT=http
export MCP_HOST=127.0.0.1  # Optional, defaults to 127.0.0.1
export MCP_PORT=8080       # Optional, defaults to 8080

# Run the server
uv run python -m fmc_mcp
```

Or add to your `.env` file:

```env
MCP_TRANSPORT=http
MCP_HOST=127.0.0.1
MCP_PORT=8080
```

**Benefits of HTTP/SSE mode:**
- Multiple concurrent client connections
- Integration testing with Python MCP clients
- Health checks and monitoring
- Standard HTTP debugging tools

### Testing Connection

```bash
uv run python -c "from fmc_mcp.client import FMCClient; import asyncio; asyncio.run(FMCClient().test_connection())"
```

### Claude Desktop Integration

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fmc": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/fmc-mcp", "python", "-m", "fmc_mcp"]
    }
  }
}
```

Then restart Claude Desktop and try:

- "What version is my FMC running?"
- "List all firewall devices"
- "Find the network object for IP 192.0.2.5"
- "Are there any pending deployments?"

Deployment status returns `status: "unavailable"` when the FMC account lacks permission and
`status: "not_found"` for an unknown device filter. Neither case is reported as synchronized.

### MCP Inspector Testing

```bash
# Install MCP Inspector
npx @anthropic/mcp-inspector

# Run the server
uv run python -m fmc_mcp
```

## Development

### Running Tests

```bash
# Run all tests
uv run --extra dev python -m pytest -q

# Run with coverage
uv run --extra dev python -m pytest --cov=src/fmc_mcp --cov-report=term-missing --cov-fail-under=80 -q

# Opt-in real FMC read-only smoke (requires configured sandbox credentials)
FMC_LIVE_TEST=1 uv run --extra dev python -m pytest -q -m live
```

### Code Quality

```bash
# Linting
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .

# Type checking
uv run --extra dev python -m mypy src tests
uv run --extra dev pyright

# All configured repository hooks
uv run --extra dev pre-commit run --all-files
```

## API Rate Limits

The FMC API has strict rate limits that this server respects:

| Limit | Value | How We Handle It |
|-------|-------|------------------|
| Requests per minute | 120 | Token bucket rate limiter |
| Concurrent connections | 10 | Connection semaphore |
| Token lifetime | 30 min | Auto-refresh on 401 |
| Max token refreshes | 3 | Full re-authentication after 3 |

The server logs warnings when approaching rate limits:

- `WARNING` when token bucket drops below 20%
- `ERROR` on 429 (rate limited) responses

## Security Notes

- **Read-Only Data Plane**: FMC configuration and status operations are GET-only; FMC authentication uses the vendor-required token POST endpoints
- **SSL**: Disabled by default for lab environments; enable in production
- **Credentials**: Store in `.env`, never commit to version control
- **API User**: Create a dedicated read-only API user in FMC
- **Reporting**: Follow [SECURITY.md](SECURITY.md) for private vulnerability disclosure

## License

Apache 2.0
