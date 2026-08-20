<div align="center">

# NetLeafy Scanner

> Parallel IP/SNI discovery and real-proxy speed testing for VLESS and Trojan configs.

[![License](https://img.shields.io/github/license/Code-Leafy/NetLeafyScanner?style=flat-square&color=2DC94E)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Code-Leafy/NetLeafyScanner?style=flat-square&color=2DC94E)](https://github.com/Code-Leafy/NetLeafyScanner/stargazers)
[![Release](https://img.shields.io/github/v/release/Code-Leafy/NetLeafyScanner?style=flat-square&color=2DC94E&label=release)](https://github.com/Code-Leafy/NetLeafyScanner/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)

</div>

## Overview

NetLeafy Scanner probes IP and SNI combinations at high concurrency and validates them with real TLS and HTTP checks. In G2ray mode it spawns a local `xray-core` instance and downloads real payloads to measure actual proxy bandwidth.

## Preview

<div align="center">
<img src="assets/image.png" alt="NetLeafy Scanner" width="720">
</div>

## Features

- Up to 200+ concurrent probes with two-stage TLS/HTTP validation.
- G2ray real-proxy speed test (parses `vless://` and `trojan://` links).
- Scan modes: full IP×SNI, IP-only latency, and G2ray bandwidth.
- Hardware profiles (Low → Ultra) plus a custom mode.
- Termux support with wake-lock and low-RAM profiles.
- Results auto-saved to `~/.netleafy/`.

## Requirements

- Python 3.7+ and `curl`.
- `ip.txt` and `sni.txt` in the same folder as `scanner.py` (auto-generated if missing).
- `xray` / `xray.exe` for G2ray mode (in the folder or on `PATH`).

## Usage

```bash
git clone https://github.com/Code-Leafy/NetLeafyScanner.git
cd NetLeafyScanner
python3 scanner.py
```

Choose a performance profile, then feed the results to [NetLeafy](https://code-leafy.github.io/NetLeafy) to generate a finished config.

## Project structure

```text
NetLeafyScanner/
├── scanner.py   # Main script
├── ip.txt       # IPs, CIDR subnets, or ranges
├── sni.txt      # SNI domains to test
└── xray.exe     # Optional, for G2ray mode
```

## License

[MIT](LICENSE)

> Educational use. You are responsible for complying with local regulations.
