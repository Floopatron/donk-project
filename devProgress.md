# 🚀 Donk Development Progress

**Last Updated:** 2025-11-07
**Current Phase:** Phase 1 - Core Infrastructure
**Active Device:** HQ Pi (Raspberry Pi 5)

---

## ✅ Done (Tested)

*Features that have been implemented AND verified working by human testing*

- [x] Project structure created
- [x] Development documentation (README.md, devProgress.md)

---

## 🤖 Done (AI)

*Features implemented by Claude Code, awaiting human verification*

*Nothing here yet - start building!*

---

## 🔄 In Progress

*Currently being worked on*

### MVP - Minimal Viable Product (Current Focus)

- [ ] HQ Pi MVP Server
  - Flask server with WebSocket support (Flask-SocketIO)
  - Web UI showing list of connected collectors
  - Health check endpoint
  - Accessible via Tailscale: http://100.74.135.15:5000

- [ ] Collector MVP Agent
  - Connects to HQ Pi via WebSocket (Tailscale)
  - Registers with unique device_id (hostname-based)
  - Auto-reconnect with exponential backoff
  - Heartbeat/keepalive mechanism
  - Graceful shutdown

- [ ] Git repository setup
  - Initialize repo on HQ Pi
  - Add .gitignore
  - Commit MVP code
  - Ready to pull to laptop

---

## 🔴 Broken

*Features that were tested but have issues - needs fixing*

*Nothing broken yet*

**Format for broken items:**
```
- [ ] Feature name
  - Issue: Description of what's broken
  - Steps to reproduce: How to trigger the bug
  - Expected: What should happen
  - Actual: What actually happens
```

---

## 📝 Planned - Phase 1: Core Infrastructure

### HQ Pi Server (Flask Backend)

- [ ] Flask app setup with basic routing
  - Entry point: `hq-pi/flask_app/main.py`
  - Health check endpoint: `/api/health`
  - Serve static files and templates

- [ ] WebSocket Hub (Flask-SocketIO)
  - Accept connections from collectors and Donk clients
  - Route messages between components
  - Handle connect/disconnect events
  - Message validation using `shared/protocol.py`

- [ ] Plugin Loader System
  - Scan `/hq-pi/plugins/` directory
  - Load `manifest.json` for each plugin
  - Import renderer classes dynamically
  - Validate plugin structure

- [ ] Context Store (In-Memory)
  - Store latest context from each collector
  - Key by `device_id` + `plugin_id`
  - Retrieve context for UI rendering
  - Optional: persist to JSON on shutdown

- [ ] Basic Web UI (PWA Shell)
  - Serve `templates/index.html`
  - WebSocket client connection
  - Display connection status
  - Simple debug view of incoming context

### Collector Agent

- [ ] Collector daemon setup
  - Main loop: `collector/collector.py`
  - Load config from `config.json`
  - Connect to HQ Pi via WebSocket (Tailscale)
  - Heartbeat/keepalive mechanism

- [ ] Plugin Loader (Collector Side)
  - Scan `/collector/plugins/` directory
  - Load `manifest.json` for each plugin
  - Import collector classes dynamically
  - Validate plugin dependencies

- [ ] Context Aggregator
  - Collect data from all loaded plugins
  - Combine into single context update message
  - Send to HQ Pi at configured interval
  - Handle errors gracefully (don't crash if plugin fails)

- [ ] Command Executor
  - Receive command messages from HQ Pi
  - Route to appropriate plugin
  - Execute plugin method or script
  - Return result to HQ Pi

### Example Plugins

- [ ] System Monitor Plugin
  - **Collector:** CPU usage, RAM usage, disk space (using `psutil`)
  - **Renderer:** Display gauges/progress bars for each metric
  - Update every 5 seconds
  - No commands (read-only)

- [ ] Active Window Plugin (Platform-Specific)
  - **Collector:** Get active window title and process name
    - Windows: `pywin32`
    - macOS: `AppKit` or `pyobjc`
    - Linux: `python-xlib` or `ewmh`
  - **Renderer:** Display current app name and window title
  - Update every 2 seconds
  - No commands (read-only)

- [ ] Audio Control Plugin
  - **Collector:** Get system volume, mute status
    - Windows: `pycaw`
    - macOS: `osascript`
    - Linux: `pulsectl` or `alsa`
  - **Renderer:** Volume slider, mute toggle button
  - Commands: `set_volume`, `toggle_mute`
  - Update every 3 seconds or on change

### Shared Protocol

- [ ] Message format definitions (`shared/protocol.py`)
  - Define all message types as dataclasses or Pydantic models
  - `ContextUpdate`, `Command`, `CommandResult`, `PageUpdate`
  - Validation functions
  - Serialization helpers (to/from JSON)

- [ ] Plugin manifest schema (`shared/plugin_schema.json`)
  - JSON Schema for `manifest.json`
  - Validation script
  - Example manifests

### Testing & Validation

- [ ] Test WebSocket connection (HQ Pi ↔ Collector)
  - Collector connects successfully
  - Heartbeat works
  - Messages route correctly

- [ ] Test plugin loading (both sides)
  - Plugins discovered automatically
  - Manifests parsed correctly
  - Classes instantiated without errors

- [ ] Test end-to-end data flow
  - Collector gathers system monitor data
  - Sends context to HQ Pi
  - HQ Pi renders UI
  - UI visible in browser at `http://100.74.135.15:5000`

- [ ] Test command execution
  - Send volume change from browser UI
  - Command routed to collector
  - Volume actually changes on collector device
  - Result returned to HQ Pi
  - UI updates to reflect new state

---

## 📝 Planned - Phase 2: Plugin Framework

- [ ] Plugin manifest versioning
- [ ] Plugin dependency management (pip install)
- [ ] Plugin security (SHA256, signatures)
- [ ] More example plugins (GitHub, Discord, Spotify)
- [ ] Plugin marketplace concept
- [ ] Hot-reload plugins without restarting

---

## 📝 Planned - Phase 3: Avatar & UI Polish

- [ ] Lottie animation system
- [ ] Avatar state machine (idle, alert, excited, etc.)
- [ ] Plugin-triggered animations
- [ ] UI theming (dark mode, accent colors)
- [ ] Touch gesture support (swipe between pages)
- [ ] Physical control mapping (future, needs hardware)

---

## 📝 Planned - Phase 4: Hardware Integration

*Waiting for Donk Pi 4 hardware to arrive*

- [ ] Assemble Donk hardware
- [ ] Deploy PWA to Donk Pi
- [ ] Physical controls (joysticks, buttons)
- [ ] Battery monitoring
- [ ] Charging dock integration
- [ ] Kiosk mode setup (Chromium fullscreen)

---

## 📝 Planned - Phase 5: Zero-Setup Control

- [ ] RP2040 USB HID co-processor setup
- [ ] USB composite gadget (keyboard + mouse + network)
- [ ] Auto-open browser via HID keystrokes
- [ ] WebRTC signaling server on HQ Pi
- [ ] coturn TURN relay setup
- [ ] Screen streaming (target → Donk)
- [ ] Bluetooth HID pairing

---

## 📝 Planned - Phase 6: Advanced Peripherals

- [ ] IR blaster (transmit/receive)
- [ ] IR code learning mode
- [ ] NFC/RFID reader (read/write)
- [ ] SubGHz radio (CC1101 TX/RX)
- [ ] Signal capture/replay

---

## 🎯 Quick Stats

- **Total Features Planned:** 45+
- **Completed (Tested):** 2
- **In Progress:** 0
- **Broken:** 0
- **Phase 1 Remaining:** 21

---

## 📊 Development Velocity

*Track how fast we're shipping - updated weekly*

| Week | Features Completed | Features Broken | Notes |
|------|-------------------|-----------------|-------|
| Week 1 (Nov 7) | 2 | 0 | Project setup |

---

## 💡 Notes for Future Sessions

**Current Focus:** Building HQ Pi Flask server with WebSocket hub

**Next Steps:**
1. Set up Flask app with basic routing
2. Implement WebSocket hub with Flask-SocketIO
3. Create shared protocol definitions
4. Build simple collector that sends test data

**Blockers:** None currently

**Questions/Decisions Needed:**
- Which OS to target first for collector? (Windows/macOS/Linux)
- Should we use Pydantic for message validation or keep it simpler?
- Store context in memory only or add Redis option early?

---

**Remember:** Features only move to "Done (Tested)" after human verification! 🧪
