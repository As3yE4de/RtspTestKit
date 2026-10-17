# RtspTestKit

## About Tool

The command-line toolkit (CLI) for **penetration testing of RTSP services** includes modules:
- **enum** - Detects existing RTSP paths on the target
- **relay** - Real-time MITM tap, forwarding the RTSP stream between client and server

---

## Disclaimer

**This tool is intended for authorized security testing only.**

Do not use this tool against systems you do not own or do not have
explicit written permission to test. Unauthorized scanning may violate
criminal law in many jurisdictions.

The author accepts no responsibility for misuse or damages caused by
this tool. See [DISCLAIMER.md](DISCLAIMER.md) for full terms.

---

## Table of Contents

- [[#Installation]]
- [[#Quick Start]]
- [[#Modules]]
	- [[#enum]]
	- [[#relay]]
- [[#Notes]]
- [[#Contributing]]
- [[#License]]
- [[#Legal]]

---

## Installation

Run the following commands on the Terminal to clone this repo and install the required packages:

```bash
$ git clone https://github.com/As3yE4de/RtspTestKit.git
$ cd RtspTestKit
$ sudo bash scripts/install.sh
```

---

## Quick Start

```bash
$ sudo python rtsp_tk.py --help
```

---

## Modules

---

### enum

A fast, multi-threaded RTSP path enumerator for authorized security testing.
This module probes IP cameras and RTSP servers for common stream paths,
helping penetration testers and security researchers enumerate exposed
endpoints during authorized engagements.

#### Features

- Multi-threaded scanning - fast enumeration of large wordlists
- Built-in default wordlist, or supply your own
- Customizing probes with RTSP methods: OPTIONS, DESCRIBE, SETUP, PLAY, etc.
- Support RTSP over TLS and authentication (`--username` / `--password`)
- Output - console and TSV file

#### Usage

- Enumerate RTSP path by specifying target `--target`, RTSP port `--port` and a wordlist `--wordlist`.

```bash
$ sudo python rtsp_tk.py enum --target 192.168.64.220 --port 8554 --wordlist wordlists/stream_paths.txt
```

- For RTSP over TLS, add option `--tls`.

```bash
$ sudo python rtsp_tk.py enum --target 192.168.64.220 --port 8322 --wordlist wordlists/stream_paths.txt --tls
```

- We can save the result to TSV file by specifying option `--output`.

```bash
$ python RtspEnum.py --target 192.168.64.220 --port 8554 --wordlist wordlists/stream_paths.txt --output output.tsv
```

- If we have valid credentials for RTSP access, use options `--username` and `--password` to enumerate paths.

```bash
$ python RtspEnum.py --target 192.168.64.220 --port 8554 --wordlist wordlists/stream_paths.txt --username admin --password admin
```

- To reduce noise, use `--found-only` which displays only responses with status code 200/401/403/454/455.

---

### relay

This module acts as a Man-in-the-Middle (MITM) specifically for the RTSP/RTP/RTCP online video/audio streaming protocol.

This tool allows capturing, analyzing, and forwarding media streams from an RTSP server (camera/IP TV) to an RTSP client (VLC, DVR, browser) without interrupting the original connection. Simultaneously, it creates a "copy" of the video/audio stream (mirror) and plays it directly on the tester's machine via `ffplay`.

#### Features

- Multi-protocol support: Automatically detects and processes both transmission modes: RTP over UDP (common) and RTP over TCP (Interleaved).
- Multimedia (A/V) support: Separates and processes video and audio streams independently, ensuring real-time synchronization during playback.
- Stream protection (SSRC Lock): Automatically locks the server's valid SSRC to prevent packet injection or interference from other streams.
- Automatic Initialization & Cleanup: Automatically configures `iptables`, enables IP Forwarding, configures network buffers, and automatically cleans up all rules when the user exits (Ctrl+C).
- Intuitive display: Detailed real-time logs (number of RTP packets, RTCP packets, filtered packets, dropped packets).
- Only support RTSP currently.

#### Usage

- To mirror RTP data from the server to the client, specify the interface which receives data from the server and forwards to the client `--iface`, specify the IP address of the server and the client with `--server` and `--client`, specify the RTSP port of the server `--rtsp-port`, and the local port which `ffplay` gonna listen on `--viewer-port`.

```bash
$ sudo python rtsp_tk.py relay --iface eth0 --server 192.168.64.220 --client 192.168.64.10 --rtsp-port 8554 --viewer-port 50000
```

---

## Notes

- The local machine should be MiTM before running the module relay.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue
first to discuss what you would like to change.

---

## License

MIT - see [LICENSE](LICENSE).

---

## Legal

This tool is provided for **authorized security testing and educational
purposes only**. Users are solely responsible for complying with all
applicable laws in their jurisdiction. See [DISCLAIMER.md](DISCLAIMER.md).