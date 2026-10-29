# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-29

### Added

#### Module brute

- Multi-threaded brute-forcing with custom timeout and delay.
- RTSP over TLS (RTSPS) port is supported.
- Output can be saved to TSV file or display directly on the console.
- Credentials can be supplied as a single credential or can be supplied via wordlists.

#### Module scan

- Multi-threaded scanning with custom timeout and delay.
- RTSP over TLS (RTSPS) port is supported.
- Output can be saved to TSV file or display directly on the console.

### Removed

- Remove option `--no-color` of all modules.

## [0.1.0] - 2026-10-18

### Added

#### Module enum

- Multi-threaded scanning - fast enumeration of large wordlists (--threads)
- Built-in default wordlist, or supply your own (--wordlist)
- Customizing probes with RTSP methods: OPTIONS, DESCRIBE, SETUP, PLAY, etc. (--method)
- Support RTSP over TLS (--tls) and authentication (--username / --password)
- Output - console and TSV file (--output)

#### Module relay

- Multi-protocol support: Automatically detects and processes both transmission modes: RTP over UDP (common) and RTP over TCP (Interleaved).
- Multimedia (A/V) support: Separates and processes video and audio streams independently, ensuring real-time synchronization during playback.
- Stream protection (SSRC Lock): Automatically locks the server's valid SSRC to prevent packet injection or interference from other streams.
- Automatic Initialization & Cleanup: Automatically configures iptables, enables IP Forwarding, configures network buffers, and automatically cleans up all rules when the user exits (Ctrl+C).
- Intuitive display: Detailed real-time logs (number of RTP packets, RTCP packets, filtered packets, dropped packets).
- Only support RTSP currently.

[0.2.0]: https://github.com/As3yE4de/RtspTestKit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/As3yE4de/RtspTestKit/releases/tag/v0.1.0
