"""
Handles device discovery for Lumagen integration over the network.

Uses multicast UDP to find iTach devices, then verifies Lumagen connectivity
through a TCP connection using the LumagenController class.
"""

import asyncio
import logging
import socket

from lumagen import LumagenDevice

_LOG = logging.getLogger(__name__)

UDP_DISCOVERY_PORT = 9131
ITACH_PORT = 4999
ITACH_MULTICAST_IP = "239.255.250.250"
MULTICAST_INTERFACE_IP = "0.0.0.0"

async def discover_itach_devices(timeout: int = 30) -> str | None:
    """
    Discover iTach devices over multicast and return the IP of a Lumagen device if available.

    Args:
        timeout (int): How long to listen for multicast packets (in seconds).

    Returns:
        str | None: IP address of a verified Lumagen device, or None if not found.
    """
    sock = None
    start = asyncio.get_running_loop().time()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.bind(("", UDP_DISCOVERY_PORT))

        mreq = socket.inet_aton(ITACH_MULTICAST_IP) + socket.inet_aton(MULTICAST_INTERFACE_IP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1.0)

        _LOG.debug("Listening for iTach discovery packets on UDP port %d", UDP_DISCOVERY_PORT)

        while asyncio.get_running_loop().time() - start < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                try:
                    response = data.decode().strip()
                except UnicodeDecodeError:
                    _LOG.warning("Received malformed data, ignoring.")
                    continue

                if "iTach" in response:
                    host = addr[0]
                    _LOG.info("Found iTach at %s", host)
                    if await validate_lumagen(host):
                        _LOG.info("Lumagen is alive at %s", host)
                        return host

            except socket.timeout:
                await asyncio.sleep(0)

    except OSError as e:
        _LOG.error("Socket error in iTach listener: %s", e)
    except asyncio.CancelledError:
        _LOG.debug("iTach listener task was cancelled")
        raise
    finally:
        if sock:
            sock.close()
        _LOG.debug("iTach listener stopped")

    return None

async def validate_lumagen(host: str) -> bool:
    """
    Check if a Lumagen device is alive at the given host using TCP connection.

    Args:
        host (str): IP address of the device to check.

    Returns:
        bool: True if device responds to is_alive check, False otherwise.
    """
    _LOG.info("Checking if Lumagen device is alive at %s:%d", host, ITACH_PORT)
    conn = LumagenDevice(host, ITACH_PORT, discovery=True)
    if not await conn.connect():
        return False

    try:
        await asyncio.sleep(1)
        return conn.is_alive
    finally:
        await conn.disconnect()
