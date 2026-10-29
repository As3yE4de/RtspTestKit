# RtspTestKit

## About Tool

The command-line toolkit (CLI) for **penetration testing of RTSP services** includes modules:
- **enum** - Detects existing RTSP paths on the target
- **relay** - Real-time MITM tap, forwarding the RTSP stream between client and server
- **brute** - Brute-forcing authentication on RTSP server
- **scan** - Scanning and looking for only open ports which have RTSP service running

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

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Modules](#modules)
	- [enum](#enum)
	- [relay](#relay)
	- [brute](#brute)
	- [scan](#scan)
- [Notes](#notes)
- [Contributing](#contributing)
- [License](#license)
- [Legal](#legal)

---

## Installation

```bash
# Cloning this repo to the local machine
$ git clone https://github.com/As3yE4de/RtspTestKit.git
$ cd RtspTestKit

# Update apt database and install required packages
$ sudo apt update
$ sudo apt install -y iptables ffmpeg python3.14 python3.14-venv python3.14-dev build-essential libnfnetlink-dev libnetfilter-queue-dev

# Create virtual environment for python3.14
$ sudo python3.14 -m venv .venv
$ source .venv/bin/activate

# Install required module for the tool
$ sudo .venv/bin/python -m pip install --upgrade pip
$ sudo .venv/bin/python -m pip install ping3
$ sudo .venv/bin/python -m pip install netfilterqueue
$ sudo .venv/bin/python -m pip install scapy

# Create an alias for the tool.
$ FILE="$(echo $HOME)/.$(basename $SHELL)rc"
$ PYVENV=$(which python)
$ echo "alias rtsp_tk='sudo $PYVENV $(pwd)/rtsp_tk.py'" >> $FILE
$ source $FILE
```

---

## Quick Start

```bash
$ rtsp_tk --help
```

---

## Modules

---

### enum

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
$ rtsp_tk enum --target 192.168.64.220 --port 8554 --wordlist wordlists/stream_paths.txt
```

- For RTSP over TLS, add option `--tls`.

```bash
$ rtsp_tk enum --target 192.168.64.220 --port 8322 --wordlist wordlists/stream_paths.txt --tls
```

- We can save the result to TSV file by specifying option `--output`.

```bash
$ rtsp_tk enum --target 192.168.64.220 --port 8554 --wordlist wordlists/stream_paths.txt --output output.tsv
```

- If we have valid credentials for RTSP access, use options `--username` and `--password` to enumerate paths.

```bash
$ rtsp_tk enum --target 192.168.64.220 --port 8554 --wordlist wordlists/stream_paths.txt --username admin --password admin
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
$ rtsp_tk relay --iface eth0 --server 192.168.64.220 --client 192.168.64.10 --rtsp-port 8554 --viewer-port 50000
```

### brute

This module is used to perform brute-forcing weak credentials on RTSP server.

#### Features

- Multi-threaded brute-forcing with custom timeout and delay.
- RTSP over TLS (RTSPS) port is supported.
- Output can be saved to TSV file or display directly on the console.
- Credentials can be supplied as a single credential or can be supplied via wordlists.

---

#### Usage

- To brute-force credential on the server, specify `--target` and the valid path `--path`, the default port is 554 for RTSP or 322 if `--tls` is specified.

```bash
$ rtsp_tk brute --target 192.168.64.220 --path "/stream/1" --username admin --pass-file wordlists/passwords.txt
```

- If the RTSP port is a custom port on the target, specify `--port`.

```bash
$ rtsp_tk brute --target 192.168.64.220 --port 8554 --path "/stream/1" --user-file wordlists/usernames.txt --pass-file wordlists/passwords.txt
```

- If we want to stop brute-forcing whenever a valid credential is found, specify `--stop-on-succeed`.

```bash
$ rtsp_tk brute --target 192.168.64.220 --path "/stream/1" --username admin --pass-file wordlists/passwords.txt --stop-on-succeed
```

### scan

This module is used to only scan for RTSP port which is opening on the target.

#### Features

- Multi-threaded scanning with custom timeout and delay.
- RTSP over TLS (RTSPS) port is supported.
- Output can be saved to TSV file or display directly on the console.

#### Usage

- If we want to check if a specific port on the target is RTSP port, specify the port number for `--port`.

```bash
$ rtsp_tk scan --target 192.168.64.220 --port 8554
```

- The `--port` option also supports a list of port separated by commas or a continuous range.

```bash
$ rtsp_tk scan --target 192.168.64.220 --port 554,8554,332
$ rtsp_tk scan --target 192.168.64.220 --port 4000-5000
```

- For a fast scanning, specify "common" for `--port` option; otherwise, "full" for port 1 to port 65535.

```bash
$ rtsp_tk scan --target 192.168.64.220 --port common
$ rtsp_tk scan --target 192.168.64.220 --port full
```

- By default, the module checks the connection by pinging to the target, specify `--no-ping` to skip checking.

## Notes

For module `relay`:
- The local machine should be MiTM before running the module relay.
- Package `iptables` and `ffmpeg` are required.

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
