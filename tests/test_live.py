"""Live integration tests against Cisco FMC Sandbox."""

import asyncio
import json


async def run_live_tests() -> None:
    """Run comprehensive tests against the FMC sandbox."""
    from fmc_mcp.client import FMCClient
    from fmc_mcp import resources, tools

    print("=" * 60)
    print("FMC MCP Server - Live Integration Tests")
    print("=" * 60)

    async with FMCClient() as client:
        resources.set_client(client)

        # Test 1: Server Version
        print("\n[TEST 1] Server Version (fmc://system/info)")
        print("-" * 40)
        try:
            version = await client.get_server_version()
            print(f"✅ Server Version: {json.dumps(version, indent=2)}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 2: List Devices
        print("\n[TEST 2] Device Records (fmc://devices/list)")
        print("-" * 40)
        try:
            devices = await client.get_devices()
            print(f"✅ Found {len(devices)} devices")
            for d in devices[:5]:  # Show first 5
                print(f"   - {d.get('name', 'Unknown')}: {d.get('hostName', 'N/A')}")
            if len(devices) > 5:
                print(f"   ... and {len(devices) - 5} more")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 3: Network Objects
        print("\n[TEST 3] Network Objects (fmc://objects/network)")
        print("-" * 40)
        try:
            networks = await client.get_network_objects()
            print(f"✅ Found {len(networks)} network objects")
            for n in networks[:5]:
                print(f"   - {n.get('name', 'Unknown')}: {n.get('value', 'N/A')}")
            if len(networks) > 5:
                print(f"   ... and {len(networks) - 5} more")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 4: Host Objects
        print("\n[TEST 4] Host Objects")
        print("-" * 40)
        try:
            hosts = await client.get_host_objects()
            print(f"✅ Found {len(hosts)} host objects")
            for h in hosts[:5]:
                print(f"   - {h.get('name', 'Unknown')}: {h.get('value', 'N/A')}")
            if len(hosts) > 5:
                print(f"   ... and {len(hosts) - 5} more")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 5: Deployable Devices
        print("\n[TEST 5] Deployment Status (fmc://deployment/status)")
        print("-" * 40)
        try:
            deployable = await client.get_deployable_devices()
            print(f"✅ Found {len(deployable)} deployable devices")
            for d in deployable[:5]:
                status = "needs deploy" if not d.get("upToDate") else "in sync"
                print(f"   - {d.get('name', 'Unknown')}: {status}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 6: MCP Resource - System Info
        print("\n[TEST 6] MCP Resource: get_system_info()")
        print("-" * 40)
        try:
            result = await resources.get_system_info()
            data = json.loads(result)
            print(f"✅ Resource returned valid JSON with {len(data)} keys")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 7: MCP Resource - List Devices
        print("\n[TEST 7] MCP Resource: list_devices()")
        print("-" * 40)
        try:
            result = await resources.list_devices()
            data = json.loads(result)
            print(f"✅ Resource returned {data.get('count', 0)} devices")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 8: MCP Tool - Search by IP (if hosts exist)
        print("\n[TEST 8] MCP Tool: search_object_by_ip()")
        print("-" * 40)
        try:
            # Try searching for a common IP
            result = await tools.search_object_by_ip("10.0.0.1")
            data = json.loads(result)
            print(f"✅ Search for 10.0.0.1: {data.get('count', 0)} matches")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 9: MCP Tool - Deployment Status
        print("\n[TEST 9] MCP Tool: check_deployment_status()")
        print("-" * 40)
        try:
            result = await tools.check_deployment_status()
            data = json.loads(result)
            print(f"✅ Status: {data.get('summary', 'Unknown')}")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("Live Integration Tests Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_live_tests())
