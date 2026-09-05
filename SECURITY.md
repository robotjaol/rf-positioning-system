# Security

This project is an engineering prototype for local experiments. The default HTTP transport is intentionally simple so a phone can connect to a laptop on a private LAN. It does not provide authentication or transport encryption.

Do not expose the backend directly to the public internet. If remote access is required, place it behind an authenticated TLS reverse proxy or VPN.

Report security issues privately to the repository owner rather than publishing exploitation details in an issue.
