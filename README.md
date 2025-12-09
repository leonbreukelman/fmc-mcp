# MCP Server for Cisco FMC

A read-only Model Context Protocol (MCP) server for Cisco Firepower Management Center (FMC) 7.4.x.

This server allows LLMs like Claude to query your firewall configuration, search for network objects, and check deployment status—all through natural language.

## Features

- **Read-Only Access**: Safe exploration of FMC configuration without modification risk
- **Rate Limiting**: Built-in token bucket rate limiter (120 req/min, 10 concurrent connections)
- **Automatic Token Refresh**: Handles FMC's 30-minute token expiration and 3-refresh limit
- **Transparent Pagination**: Automatically fetches all pages from large datasets

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

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Access to a Cisco FMC 7.4.x instance

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/fmc-mcp.git
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
| `FMC_VERIFY_SSL` | No | `false` | SSL certificate verification |
| `FMC_DOMAIN_UUID` | No | auto | Domain UUID (auto-discovered) |
| `FMC_TIMEOUT` | No | `60` | Request timeout in seconds |

## Usage

### Running the Server

```bash
# Using uv
uv run python -m fmc_mcp

# Or using the CLI entry point
uv run mcp-server-fmc
```

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
- "Find the network object for IP 10.10.10.5"
- "Are there any pending deployments?"

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
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/fmc_mcp --cov-report=term-missing
```

### Code Quality

```bash
# Linting
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
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

- **Read-Only**: This server only performs GET requests
- **SSL**: Disabled by default for lab environments; enable in production
- **Credentials**: Store in `.env`, never commit to version control
- **API User**: Create a dedicated read-only API user in FMC

## License

Apache 2.0
