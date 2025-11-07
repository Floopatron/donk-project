# 🧠 Donk: Technical Specification v2.0

**Version:** 2.0 (Updated with AI feedback corrections)
**Date:** 2025-11-07
**Status:** Active Development

---

## 📘 Executive Overview

Donk is a modular, context-aware handheld control surface powered by DonkOS - a distributed architecture for device control and context aggregation.

**Three Components:**
1. **HQ Pi** - Central server (Raspberry Pi 5) - Flask backend, WebSocket hub, plugin renderer
2. **Donk** - Handheld client (Raspberry Pi 4) - Touchscreen, physical controls, wireless peripherals
3. **Collectors** - Desktop/laptop agents - Gather context, execute commands

---

## 🎯 Design Goals

- **6+ hour battery life** for mobile operation
- **Zero-setup device control** - plug in once, control wirelessly
- **Full context awareness** of all connected devices
- **Modular plugin architecture** with hot-reload
- **Expressive UI** with avatar personality
- **Multi-modal wireless** - WiFi, Bluetooth, SubGHz, IR, NFC

---

## 🔩 Hardware Specification

### Donk Handheld (Future Build)

| Component | Specification | Power | Cost |
|-----------|--------------|-------|------|
| **SBC** | Raspberry Pi 4 (4GB) | 4-6W | $55 |
| **Display** | Waveshare 5.5" AMOLED 1920×1080 | 2-4W | $80 |
| **Battery** | 4× 18650 (2S2P, 7.4V 6Ah, 44Wh) | - | $24 |
| **BMS** | 2S 20A Battery Management | - | $8 |
| **Buck Converter** | 7.4V → 5V @ 5A (95% eff) | - | $6 |
| **USB Co-Processor** | RP2040 Pico (HID gadget) | 0.2W | $4 |
| **Audio HAT** | I2S 3W Stereo + MEMS mic | 0.2W | $22 |
| **SubGHz Radio** | CC1101 (300-928MHz TX/RX) | 0.5W | $8 |
| **NFC/RFID** | PN532 breakout | 0.2W | $15 |
| **IR TX/RX** | LED + TSOP38238 | 0.1W | $5 |
| **Controls** | 2× joysticks, 12× buttons, 2× encoders | - | $45 |
| **Cooling** | 40mm fan + heatsink | 0.5W | $12 |
| **Misc** | Pogo pins, 3D print, wiring | - | $40 |

**Total Cost:** ~$404
**Power Budget:** 7.5W average → **5.9 hours runtime** (conservative: 5.5hr)

**To hit 6+ hours:** Use 3S2P (6 cells) = 66Wh → 6.3hr+ runtime

---

### HQ Pi (Current Device - Already Configured)

- **Hardware:** Raspberry Pi 5 (8GB)
- **Network:** WiFi + Ethernet + Tailscale (100.74.135.15)
- **Storage:** 32GB microSD (12GB free)
- **Software:** Python 3.11.2, Flask 2.2.2, Tailscale 1.90.6
- **Role:** Always-on server, WebSocket hub, plugin renderer

---

## 🏗️ System Architecture

### Network Topology

```
                    Tailscale VPN Mesh
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    HQ Pi              Collector 1        Collector 2
(100.74.135.15)       (Desktop)           (Laptop)
        │
        │ WiFi (local network)
        ▼
      Donk
  (Handheld)
```

### Data Flow

```
Collector: Gather context → Send via WSS → HQ Pi
HQ Pi: Receive context → Render UI → Send to Donk
Donk: Display UI → User action → HQ Pi → Route to Collector
Collector: Execute command → Return result → HQ Pi → Donk
```

---

## 🔌 Plugin System

### Structure

Each plugin has **TWO parts:**

1. **Collector Plugin** (`/collector/plugins/{name}/`)
   - `manifest.json` - metadata
   - `collector.py` - gathers context on target device
   - `scripts/` - shell scripts for commands

2. **HQ Renderer Plugin** (`/hq-pi/plugins/{name}/`)
   - `manifest.json` - same as collector (must match!)
   - `renderer.py` - generates UI for Donk
   - `assets/` - icons, CSS

### Manifest Schema

```json
{
  "plugin_id": "system_monitor",
  "version": "1.0.0",
  "name": "System Monitor",
  "author": "donk-official",

  "collector": {
    "file": "collector.py",
    "class": "SystemMonitorCollector",
    "update_interval": 5,
    "dependencies": ["psutil"]
  },

  "renderer": {
    "file": "renderer.py",
    "class": "SystemMonitorRenderer",
    "icon": "assets/cpu.svg"
  },

  "commands": [
    {
      "id": "restart_service",
      "name": "Restart Service",
      "script": "scripts/restart.sh",
      "confirmation": true
    }
  ]
}
```

### Communication Protocol

**WebSocket Messages (JSON):**

```python
# Collector → HQ Pi (context update)
{
  "type": "context_update",
  "device_id": "desktop-main",
  "plugin_id": "system_monitor",
  "timestamp": 1699123456,
  "data": {
    "cpu_percent": 45.2,
    "ram_percent": 67.8,
    "disk_percent": 55.1
  }
}

# HQ Pi → Collector (command)
{
  "type": "command",
  "device_id": "desktop-main",
  "plugin_id": "audio_control",
  "command_id": "set_volume",
  "args": {"level": 50}
}

# Collector → HQ Pi (result)
{
  "type": "command_result",
  "command_id": "set_volume",
  "success": true,
  "message": "Volume set to 50%"
}

# HQ Pi → Donk (UI update)
{
  "type": "page_update",
  "plugin_id": "system_monitor",
  "widgets": [
    {"type": "gauge", "label": "CPU", "value": 45.2, "max": 100},
    {"type": "gauge", "label": "RAM", "value": 67.8, "max": 100}
  ]
}
```

---

## 🌐 Zero-Setup Device Control

### Tier 1: Persistent Devices (Full Context)

**Use Case:** Your own devices (desktop, laptop)

**Setup:** One-time install of collector agent + Tailscale

**Features:**
- Full context awareness (active window, audio, running apps)
- Bidirectional commands
- Plugin ecosystem
- Works remotely via Tailscale

---

### Tier 2: Zero-Setup Devices (Ad-Hoc Control)

**Use Case:** Guest laptops, friend's PC, smart TVs

#### Method A: USB HID + Screen Viewing (Primary)

**IMPORTANT:** Pi 4B USB-C port is HOST-ONLY, not OTG-capable!

**Solution:** RP2040 Pico as USB Co-Processor

```
┌──────────────┐  UART   ┌──────────────┐  USB-C  ┌──────────────┐
│   Donk Pi4   │ ←─────→ │  RP2040 Pico │ ←─────→ │ Target Device│
│ (Controller) │         │ (HID Gadget) │         │   (Laptop)   │
└──────────────┘         └──────────────┘         └──────────────┘
                                 ↓
                         HID Keyboard/Mouse
                         + USB Ethernet (optional)
```

**Wiring:**
- Pi 4 GPIO 14 (TX) → Pico GPIO 1 (RX)
- Pi 4 GPIO 15 (RX) → Pico GPIO 0 (TX)
- Pi 4 5V → Pico VSYS
- Pico USB-C → Target device

**Flow:**

1. **Plug USB** - RP2040 presents as HID keyboard/mouse (+ network adapter)
2. **Auto-open browser** (optional) - RP2040 sends keystrokes to open incognito browser → `http://192.168.7.1/view`
3. **Screen viewing** - Browser requests screen capture (WebRTC) → streams to Donk
4. **Control** - Donk joystick → Pi 4 → UART → RP2040 → USB HID
5. **Wireless viewing** - After WebRTC established, unplug USB → screen stream continues via WiFi
6. **Control remains wired** - For wireless control, pair Bluetooth HID separately

**Note:** Browser CANNOT control OS globally (JavaScript sandbox). HID is required for actual mouse/keyboard control.

---

#### Method B: Bluetooth HID

**Setup:** 30sec one-time pairing

**Use Case:** Devices without USB or prefer wireless

**Latency:** 20-50ms (acceptable)

---

#### Method C: IR Blaster

**Setup:** Zero - just point and click

**Use Case:** TVs, ACs, projectors, set-top boxes

**Range:** 10m line-of-sight

---

#### Method D: SubGHz Radio

**Hardware:** CC1101 transceiver (300-928 MHz)

**Use Case:** Garage doors, car fobs, 433MHz outlets, weather stations

**Range:** 500m+ with good antenna

---

## 🎨 User Interface

### Frontend Stack

- **Rendering:** Chromium WebView (kiosk mode, fullscreen)
- **Framework:** Vanilla JS + Web Components
- **Styling:** CSS3 + CSS Variables (theming)
- **Animation:** Lottie-web (avatar)
- **Communication:** WebSocket (Socket.IO client)

### Page Layout

```
┌──────────────────────────────────────────────────┐
│  [Avatar]              [Time] [WiFi] [Battery]   │
├──────────────────────────────────────────────────┤
│  ◄ System │ Audio │ GitHub │ Discord │ Browser ►│
├──────────────────────────────────────────────────┤
│                                                  │
│           PLUGIN PAGE CONTENT                    │
│           (widgets rendered by HQ Pi)            │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Widget Types

```javascript
const WIDGETS = {
  // Display
  'label': { text, icon, color },
  'gauge': { value, min, max, unit },
  'progress_bar': { value, max, label },
  'list': { items: [{title, subtitle, icon}] },

  // Interactive
  'button': { label, icon, action, confirm },
  'toggle': { label, value, action },
  'slider': { label, value, min, max, action }
};
```

### Avatar System

**States:**
- **Idle** - Default, breathing/blinking
- **Sleep** - No activity 5min
- **Alert** - Context change
- **Excited** - Positive event (PR merged, CI pass)
- **Sad** - Negative event (CI fail, error)
- **Working** - Command executing

**Implementation:** Lottie JSON animations (60fps on Pi 4)

---

## 🔐 Security

### Network
- Tailscale WireGuard encryption (Tier 1)
- WSS (WebSocket Secure) with TLS
- TURN relay on HQ Pi (coturn)

### Authentication
- HQ Pi: HTTP Basic Auth (username + bcrypt password)
- Collectors: API key per device
- Donk: Shared secret (embedded in config)

### Plugin Security
- SHA256 hash verification
- RSA signatures (optional, for official plugins)
- User approval before pip install

---

## ⚡ Performance

### HQ Pi (Expected Load)

- **Connections:** 10 collectors + 1 Donk
- **Messages:** ~10-20 req/sec
- **CPU:** 10-20% (Pi 5 @ 2.4GHz)
- **RAM:** 200-500MB
- **Network:** ~10KB/sec

**Optimizations:**
- Async I/O (eventlet/gevent)
- Context diffing (only send changes)
- Rate limiting (max 10 updates/sec per collector)
- gzip compression for large messages

### Donk Client

- **Target:** 60fps UI, 30fps WebRTC video
- **GPU:** Hardware acceleration (VideoCore VII)
- **Power Optimization:**
  - Auto-dim display after 30s
  - CPU governor: conservative (600MHz-1.8GHz)
  - WiFi power save mode
  - Disable unused radios

---

## 📁 Project Structure

```
/donk-project/
├── README.md              # Dev workflow guide
├── devProgress.md         # Feature tracking (AI + human signoff)
├── docs/
│   └── TECHNICAL_SPEC.md  # This file
├── hq-pi/                 # Flask server
│   ├── flask_app/
│   ├── plugins/
│   ├── static/
│   └── templates/
├── collector/             # Desktop agent
│   ├── collector.py
│   ├── plugins/
│   └── config.json
├── donk-device/           # Handheld (future)
│   ├── donk_client.py
│   ├── usb_gadget/
│   └── hardware/
├── shared/                # Common code
│   ├── protocol.py
│   └── plugin_schema.json
└── tests/
```

---

## 🚀 Development Roadmap

### Phase 1: Core Infrastructure (Weeks 1-2) - **CURRENT**

- HQ Pi Flask server + WebSocket hub
- Collector agent with plugin loader
- System monitor plugin (example)
- Basic PWA (test in browser)
- Test: Control desktop from browser

---

### Phase 2: Plugin Framework (Weeks 3-4)

- Plugin manifest system
- Dynamic loading
- Example plugins: Audio, GitHub, Discord
- Command execution
- Security (SHA256, signatures)

---

### Phase 3: Avatar & UI Polish (Week 5)

- Lottie animation system
- Avatar state machine
- UI theming
- Touch gestures

---

### Phase 4: Hardware Integration (Weeks 6-7)

**Prerequisite:** Donk Pi 4 hardware arrives

- Assemble hardware
- Deploy PWA to Donk Pi
- Physical controls
- Battery monitoring
- Kiosk mode

---

### Phase 5: Zero-Setup Control (Week 8)

- RP2040 USB HID co-processor
- USB gadget mode
- WebRTC signaling + coturn
- Auto-open browser
- Screen streaming

---

### Phase 6: Advanced Peripherals (Weeks 9-10)

- IR blaster
- Bluetooth HID
- NFC reader
- SubGHz radio

---

### Phase 7: Polish & Deployment (Weeks 11-12)

- Installation scripts
- Configuration wizard
- Documentation
- Auto-update system

---

## 🔧 OS-Specific Capabilities

### Collector Requirements

| Feature | Windows | macOS | Linux | Permissions |
|---------|---------|-------|-------|-------------|
| Active window | ✅ pywin32 | ✅ AppKit | ✅ ewmh | macOS: Accessibility |
| Process list | ✅ psutil | ✅ psutil | ✅ psutil | None |
| System volume | ✅ pycaw | ✅ osascript | ✅ pulsectl | None |
| Per-app volume | ✅ pycaw | ❌ | ⚠️ | Windows: Admin |
| Media keys | ✅ keyboard | ✅ keyboard | ✅ keyboard | None |
| Global hotkeys | ✅ keyboard | ✅ keyboard | ✅ keyboard | macOS: Accessibility |

**Collector should:**
- Self-check capabilities on startup
- Prompt user if permissions missing
- Degrade gracefully (disable features)

---

## ⚠️ Technical Corrections (from AI Feedback)

### Critical Fixes Applied:

1. **USB Gadget Mode** - Pi 4B cannot act as USB device
   - **Fixed:** Added RP2040 Pico as USB co-processor ($4)

2. **Browser Control Limitations** - JS cannot inject OS-level input
   - **Fixed:** USB/BT HID for control, WebRTC only for screen viewing

3. **Battery Topology** - 6S too complex
   - **Fixed:** Changed to 2S2P (simpler, still 5.9hr runtime)

4. **Thermal Management** - Pi 4 throttles in sealed enclosure
   - **Fixed:** Added cooling fan + heatsink (0.5W overhead)

5. **Collector Permissions** - Windows/macOS need special access
   - **Fixed:** Added permission checking + graceful degradation

6. **Plugin Security** - Auto-pip install is risky
   - **Fixed:** SHA256 verification + user approval

---

## 💡 Key Design Decisions

1. **Pi 4 for Donk** (not Pi 5) - Better power efficiency, still plenty fast
2. **RP2040 co-processor** - Enables USB HID on Pi 4
3. **2S2P battery** - Simpler BMS, still meets 6hr target
4. **Plugin split architecture** - Collector gathers, HQ renders
5. **Tailscale VPN** - Already configured, proven mesh networking
6. **Lottie animations** - Easy for designers, 60fps on Pi 4

---

## 🎓 References

- **Tailscale VPN:** https://tailscale.com/
- **Flask-SocketIO:** https://flask-socketio.readthedocs.io/
- **Lottie Web:** https://airbnb.io/lottie/
- **RP2040 USB HID:** https://learn.adafruit.com/circuitpython-essentials/circuitpython-hid-keyboard-and-mouse
- **CC1101 SubGHz:** https://github.com/LSatan/SmartRC-CC1101-Driver-Lib

---

**End of Technical Specification**

**Next Steps:** See `devProgress.md` for current development status and `/README.md` for development workflow.
