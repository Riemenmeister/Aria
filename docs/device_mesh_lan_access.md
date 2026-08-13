# Aria Device Mesh LAN Access

This guide keeps Aria PC, Aria Laptop Zephyr, and Aria Smartphone Honor X5c on a read-only trusted-LAN path.

## Start Aria PC for LAN clients

Run from the repository root on Aria PC:

```powershell
py tools\aria_pc_server.py --host 0.0.0.0 --port 8787
```

Find the Aria PC LAN IPv4 address:

```powershell
ipconfig
```

Use only a private LAN address such as `192.168.x.x`, `10.x.x.x`, or `172.16.x.x` through `172.31.x.x`. Do not use a public IP address for this server.

## Verify from Zephyr

Open these URLs from Aria Laptop Zephyr on the same trusted LAN:

```text
http://<aria-pc-lan-ip>:8787/api/health
http://<aria-pc-lan-ip>:8787/api/device-mesh
http://<aria-pc-lan-ip>:8787/api/device/aria-laptop-zephyr
```

A successful check returns JSON and keeps `aria-laptop-zephyr` as the device id.

## Verify from Honor X5c

Open these URLs from Aria Smartphone Honor X5c on the same trusted Wi-Fi:

```text
http://<aria-pc-lan-ip>:8787/api/health
http://<aria-pc-lan-ip>:8787/api/device-mesh
http://<aria-pc-lan-ip>:8787/api/device/aria-smartphone-honor-x5c
```

A successful check returns JSON and keeps `aria-smartphone-honor-x5c` as the device id.

## Record evidence

After both remote clients can reach the server, update `reports/device_mesh_client_checklist.json` with observed timestamps and keep secrets out of the repository.

## Guardrails

- Keep the channel read-only until an authenticated write channel is explicitly implemented.
- Do not store device passwords, Wi-Fi credentials, browser cookies, or tokens.
- Do not expose this server to the public internet without authentication, firewall, and reverse-proxy review.
- Keep Actively disconnected unless the user explicitly changes scope.