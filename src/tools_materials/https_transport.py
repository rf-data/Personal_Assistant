"""Official HTTPS only, with public DNS answers pinned to the TCP destination.

HTTPX retains the original Host and TLS SNI/verification name. No proxy, redirects,
cookies or ambient credentials. Resolve again for every request; no pooled reuse.
"""

import ipaddress
import socket
from urllib.parse import urlsplit

import httpx

from src.tools_materials.inventory import official


def public_addresses(host):
    answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    addresses = []
    for family, _kind, _proto, _canon, address in answers:
        if family not in (socket.AF_INET, socket.AF_INET6):
            raise ValueError("Unsupported DNS address family")
        ip = ipaddress.ip_address(address[0])
        if (
            not ip.is_global
            or ip.is_multicast
            or ip.is_reserved
            or (
                isinstance(ip, ipaddress.IPv6Address)
                and (ip.ipv4_mapped or ip.sixtofour or ip.teredo)
            )
        ):
            raise ValueError("Nonpublic DNS destination refused")
        if str(ip) not in addresses:
            addresses.append(str(ip))
    if not addresses:
        raise ValueError("Empty DNS answer")
    return addresses


class PublicHTTPSTransport(httpx.BaseTransport):
    def __init__(self):
        self.inner = httpx.HTTPTransport(
            verify=True,
            trust_env=False,
            retries=0,
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
        )

    def handle_request(self, request):
        url = str(request.url)
        if not official(url) or urlsplit(url).fragment:
            raise ValueError("Official credential-free HTTPS URL required")
        host = request.url.host
        address = public_addresses(host)[0]
        # Connecting to a numeric address prevents a second resolution of host.
        headers = request.headers.copy()
        for name in ("authorization", "proxy-authorization", "cookie"):
            headers.pop(name, None)
        headers["Host"] = host
        pinned = httpx.Request(
            request.method,
            request.url.copy_with(host=address),
            headers=headers,
            stream=request.stream,
            extensions={**request.extensions, "sni_hostname": host},
        )
        return self.inner.handle_request(pinned)

    def close(self):
        self.inner.close()
