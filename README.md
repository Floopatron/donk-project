# 🧠 Donk Project - Development Guide

**Current Device:** HQ Pi (Raspberry Pi 5) - Central Server
**Status:** Active Development (R&D Phase)

---

## 🎯 Quick Start for Claude Code

This project is developed **using Claude Code**. When starting a new session:

1. Read this README for architecture overview
2. Check `devProgress.md` for current status
3. Review `/docs/TECHNICAL_SPEC.md` for detailed design
4. Update `devProgress.md` as you work (AI marks done → Human signs off)
5. Test your changes before marking complete

---

## 🏗️ Architecture Overview

Donk is a **distributed system** with 3 components that must work together:

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   HQ Pi (You)   │ ←─WSS─→ │   Collector(s)  │         │  Donk Handheld  │
│  Central Server │         │  Desktop Agents │ ←─WSS─→ │   (Future Pi4)  │
│   Flask + WS    │         │  Context Gather │         │   PWA Client    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        ↑                                                         ↑
        └─────────────────── WebSocket Hub ─────────────────────┘
```

### Component Responsibilities

| Component | Location | Language | Role |
|-----------|----------|----------|------|
| **HQ Pi** | `/hq-pi` | Python (Flask) | WebSocket hub, plugin renderer, TURN relay |
| **Collector** | `/collector` | Python | Runs on target devices, gathers context, executes commands |
| **Donk Device** | `/donk-device` | Python + JS | Handheld client, UI display, physical controls (future hardware) |
| **Shared** | `/shared` | Python | Common protocol definitions, utilities |

---

## 📋 Development Workflow

### The `devProgress.md` System

This project uses **`devProgress.md`** to track features:

1. **AI (Claude Code) updates** when implementing features
   - Moves items to "In Progress" when working
   - Moves to "Done (AI)" when code is complete

2. **Human tester verifies** functionality
   - Tests the feature
   - Moves to "Done (Tested)" if working
   - Moves to "Broken" if issues found

3. **Only "Done (Tested)" counts as complete**

**Format:**
```markdown
## ✅ Done (Tested)
- [x] Feature name - what it does

## 🤖 Done (AI)
- [x] Feature name - waiting for human testing

## 🔄 In Progress
- [ ] Feature name - currently being worked on

## 🔴 Broken
- [ ] Feature name - tested but has issues (describe issue)

## 📝 Planned
- [ ] Feature name - not started yet
```

### Development Flow

```
1. Pick feature from "Planned" in devProgress.md
2. Move to "In Progress"
3. Implement & test locally
4. Move to "Done (AI)"
5. Human tests
6. Human moves to "Done (Tested)" OR "Broken"
7. If broken → fix → repeat
```

---

## 🧩 Component Integration Points

**CRITICAL:** These components depend on each other. Changes must maintain compatibility.

### WebSocket Protocol (Shared Message Format)

All components communicate via WebSocket using JSON messages defined in `/shared/protocol.py`:

```python
# Collector → HQ Pi
{
  "type": "context_update",
  "device_id": "desktop-main",
  "plugin_id": "system_monitor",
  "data": {...}
}

# HQ Pi → Collector
{
  "type": "command",
  "device_id": "desktop-main",
  "plugin_id": "audio_control",
  "command_id": "set_volume",
  "args": {"level": 50}
}

# HQ Pi → Donk
{
  "type": "page_update",
  "plugin_id": "system_monitor",
  "widgets": [...]
}
```

**Rule:** If you modify message structure in one component, update ALL components + `shared/protocol.py`

### Plugin Architecture

Plugins have **TWO parts** that must match:

1. **Collector Plugin** (`/collector/plugins/{name}/collector.py`)
   - Gathers data on target device
   - Sends context to HQ Pi

2. **HQ Renderer Plugin** (`/hq-pi/plugins/{name}/renderer.py`)
   - Receives context from HQ Pi
   - Renders UI for Donk

Both must have matching `manifest.json` with same `plugin_id` and `version`.

**Rule:** When creating/updating plugins, always update both parts + manifests

---

## 🚀 Current Development Phase

**Phase 1: Core Infrastructure** (R&D on HQ Pi)

We're building the server-side components **first** because:
- Donk hardware doesn't exist yet (Pi 4 not purchased)
- Can test using desktop browser as "fake Donk"
- Collector can run on main desktop/laptop for testing

**Immediate Goals:**
1. HQ Pi Flask server with WebSocket hub
2. Basic collector agent (system monitor)
3. Simple PWA (test in browser)
4. Example plugin working end-to-end

**Testing Setup:**
```
HQ Pi (this device) ←→ Collector (desktop) ←→ Browser (fake Donk)
```

---

## 📁 Directory Structure

```
/donk-project/
├── README.md                    # You are here
├── devProgress.md              # Feature tracking (AI + Human signoff)
│
├── docs/                       # Planning & specs
│   ├── TECHNICAL_SPEC.md       # Full technical specification
│   ├── HARDWARE_GUIDE.md       # Future: hardware assembly
│   └── PLUGIN_DEV_GUIDE.md     # Future: how to write plugins
│
├── hq-pi/                      # HQ Pi server (Flask backend)
│   ├── flask_app/
│   │   ├── main.py             # Flask app entry
│   │   ├── websocket_hub.py    # WebSocket manager
│   │   ├── plugin_loader.py    # Load UI renderers
│   │   └── config.py           # Server config
│   ├── plugins/                # UI renderer plugins
│   │   └── {plugin_name}/
│   │       ├── manifest.json
│   │       ├── renderer.py
│   │       └── assets/
│   ├── static/                 # Frontend assets
│   │   ├── css/
│   │   ├── js/
│   │   └── avatars/            # Lottie animations
│   ├── templates/
│   │   └── index.html          # Donk PWA shell
│   └── requirements.txt
│
├── collector/                  # Collector agent
│   ├── collector.py            # Main daemon
│   ├── plugin_loader.py        # Load collector plugins
│   ├── context_aggregator.py  # Gather system context
│   ├── plugins/                # Collector plugins
│   │   └── {plugin_name}/
│   │       ├── manifest.json
│   │       ├── collector.py
│   │       └── scripts/
│   ├── config.json             # Device config
│   └── requirements.txt
│
├── donk-device/                # Donk handheld (future Pi 4)
│   ├── donk_client.py          # PWA client wrapper
│   ├── usb_gadget/             # USB HID via RP2040
│   ├── hardware/               # Hardware drivers
│   └── requirements.txt
│
├── shared/                     # Shared code
│   ├── protocol.py             # Message definitions
│   ├── plugin_schema.json      # Plugin manifest schema
│   └── utils.py
│
└── tests/                      # Integration tests
    ├── test_websocket.py
    └── test_plugins.py
```

---

## 🔧 Development Environment

**On HQ Pi (this device):**

```bash
# Install dependencies
cd ~/donk-project/hq-pi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run HQ Pi server
python flask_app/main.py

# Access in browser (for testing)
http://localhost:5000
```

**On Collector Device (desktop/laptop):**

```bash
# Install collector
cd ~/donk-project/collector
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp config.example.json config.json
# Edit config.json with HQ Pi Tailscale IP

# Run collector
python collector.py
```

---

## ⚠️ Important Notes for Claude Code

### When Implementing Features:

1. **Always update `devProgress.md`** as you work
2. **Test your code** before marking done
3. **Maintain WebSocket protocol compatibility** - check `shared/protocol.py`
4. **Both plugin parts** must be updated together
5. **Comment your code** - explain WHY, not just WHAT
6. **Use type hints** in Python for clarity
7. **Follow existing code style** in the project

### When Fixing Bugs:

1. Move from "Broken" → "In Progress" in `devProgress.md`
2. Describe the fix in comments
3. Test the fix thoroughly
4. Move to "Done (AI)" for human re-testing

### When User Changes Direction:

This project is **interest-driven**. If the user wants to:
- Pivot to a different feature → update `devProgress.md` accordingly
- Try something experimental → create a branch/note in progress
- Skip ahead → document what's being skipped in "Planned"

**Flexibility is key!** Adapt to what captures their interest.

---

## 🎨 Design Principles

1. **Modularity** - Components can be developed/tested independently
2. **Extensibility** - Plugin system for easy feature additions
3. **Progressive Enhancement** - Core features first, polish later
4. **User Testing** - Nothing is done until human verifies it works
5. **Documentation** - Future Claude instances should understand the code

---

## 🆘 Troubleshooting

**WebSocket connection fails:**
- Check Tailscale is running: `sudo tailscale status`
- Check HQ Pi IP: `ip addr show tailscale0`
- Check firewall: `sudo ufw status`

**Plugin not loading:**
- Verify `manifest.json` is valid JSON
- Check plugin `plugin_id` matches in both collector + HQ renderer
- Check HQ Pi logs: `tail -f logs/hq-pi.log`

**Collector can't reach HQ Pi:**
- Verify both on Tailscale network
- Ping test: `ping 100.74.135.15`
- Check WSS URL in collector `config.json`

---

## 📚 Key Documentation

- **Full Technical Spec:** `/docs/TECHNICAL_SPEC.md` - Complete design, hardware, architecture
- **Development Progress:** `devProgress.md` - What's done, in progress, broken
- **This File:** High-level dev workflow and component integration

---

## 🚢 Deployment (Future)

When Donk hardware arrives:
1. Flash Pi 4 with Raspberry Pi OS Lite
2. Copy `/donk-device` to Pi 4
3. Run setup script: `./setup_donk.sh`
4. Configure kiosk mode (Chromium fullscreen)
5. Test WebSocket connection to HQ Pi

---

**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Next Phase:** HQ Pi Flask server + basic collector
