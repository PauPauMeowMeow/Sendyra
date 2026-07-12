# Sendyra

A cross-platform app for quickly sharing text and files between devices on the same local network.

Publish a text snippet or a file to the "board" — and it instantly becomes visible to every device on the network. Any device can copy the text or download the file. No cloud, no registration, no central server.

## Features

- **Shared board** — texts and files from all devices on the network in a single list
- **Automatic device discovery** via mDNS (zeroconf)
- **Download from a browser** — devices without the app can open `http://<ip>:53317` and download files
- **Decentralized** — each device stores only its own items

## Platforms

Windows, macOS, Linux (Ubuntu/Debian/Fedora), Android, iOS.

> **iOS**: an `.ipa` build is available, but installation is only possible via sideload/TestFlight (requires an Apple Developer Account).

## Installation

Download the build for your platform from the [Releases](https://github.com/PauPauMeowMeow/Sendyra/releases) page.

- **Windows**: unpack the zip and run `Sendyra.exe`
- **macOS**: open the `.dmg`; on first launch allow the app in *System Settings → Privacy & Security* (the build is unsigned)
- **Linux**: unpack the tar.gz and run `sendyra`
- **Android**: install the `.apk` (allow installation from unknown sources)

On first launch your firewall may ask for permission to accept incoming connections — allow it, otherwise other devices will not be able to download your files.

## Running from source

```bash
git clone https://github.com/PauPauMeowMeow/Sendyra.git
cd Sendyra
pip install -e .
flet run src/main.py
```

## How it works

1. The app starts a local HTTP server (port 53317) and announces itself on the network via mDNS (`_sendyra._tcp.local.`)
2. Published texts and files are stored locally on your device
3. The UI periodically polls the boards of discovered devices and shows a combined list
4. Files are downloaded directly from the device that owns them

## Security

In the current version the exchange is open and unencrypted — use it only in trusted networks. Pairing and encryption are planned for future versions.
