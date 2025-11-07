# 🚀 Donk Quick Start Guide

**For:** Claude Code instances starting new sessions
**Goal:** Get up to speed in < 2 minutes

---

## 📚 Essential Reading Order

1. **README.md** (5 min) - Development workflow, component architecture, integration points
2. **devProgress.md** (1 min) - Current status, what's done, what's next
3. **docs/TECHNICAL_SPEC.md** (reference) - Full technical details when needed

---

## 🎯 What is Donk?

A modular, context-aware handheld control surface with 3 components:

```
HQ Pi (Flask server) ←→ Collectors (desktop agents) ←→ Donk (handheld)
     ↑                                                      ↑
  You are here                                     (Future hardware)
```

**Current Phase:** Building HQ Pi server + collector (Phase 1)
**Test Setup:** Desktop browser acts as "fake Donk"

---

## 🔑 Key Concepts

### Plugin Architecture

Every plugin has **TWO parts**:
1. **Collector Plugin** - gathers data on target device
2. **HQ Renderer Plugin** - generates UI for Donk

Both must have matching `manifest.json` with same `plugin_id`.

### WebSocket Protocol

All components talk via WebSocket using JSON messages in `shared/protocol.py`:
- Collector → HQ: context updates
- HQ → Collector: commands
- HQ → Donk: rendered UI

### devProgress.md Workflow

1. AI marks features "Done (AI)" when implemented
2. Human tests and moves to "Done (Tested)" or "Broken"
3. Only "Done (Tested)" counts as complete

**Always update devProgress.md as you work!**

---

## 🛠️ Current Development Environment

**Device:** HQ Pi (Raspberry Pi 5)
- **IP:** 192.168.1.73 (local), 100.74.135.15 (Tailscale)
- **Python:** 3.11.2
- **Flask:** 2.2.2 (already installed)
- **Tailscale:** Active ✅

**Project Location:** `~/donk-project/`

---

## 📂 Directory Structure (Quick Ref)

```
/donk-project/
├── README.md              # Read first: dev workflow
├── devProgress.md         # Track features here
├── hq-pi/                 # Flask server (current focus)
│   ├── flask_app/         # Server code
│   ├── plugins/           # UI renderers
│   └── static/            # Frontend assets
├── collector/             # Desktop agent
│   └── plugins/           # Context collectors
├── shared/                # Protocol definitions
└── docs/                  # Technical specs
```

---

## ⚡ Quick Commands

```bash
# Navigate to project
cd ~/donk-project

# Check Tailscale status
sudo tailscale status

# Test Python
python3 --version

# Install HQ Pi dependencies (when ready)
cd hq-pi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run HQ Pi server (when ready)
python flask_app/main.py
```

---

## 🎯 What to Build Next

Check `devProgress.md` → "Planned - Phase 1" section.

**Current Priority:**
1. Flask app setup with basic routing
2. WebSocket hub (Flask-SocketIO)
3. Shared protocol definitions
4. Simple collector that sends test data

---

## ⚠️ Common Gotchas

1. **USB Gadget Mode** - Pi 4B can't do this! Use RP2040 Pico co-processor
2. **Browser Control** - JavaScript CAN'T control OS globally, only HID can
3. **Plugin Parts** - Always update BOTH collector + renderer together
4. **Message Format** - Follow `shared/protocol.py` strictly
5. **devProgress** - Update as you work, don't batch updates

---

## 🧪 Testing Strategy

**Phase 1 Testing (no Donk hardware yet):**
1. Run HQ Pi server on Pi 5
2. Run collector on main desktop/laptop
3. Open browser to HQ Pi (http://100.74.135.15:5000)
4. Browser acts as "fake Donk" for UI testing

**What to Verify:**
- Collector connects to HQ Pi via WebSocket
- Context updates flow: Collector → HQ Pi
- Commands work: Browser UI → HQ Pi → Collector → executes
- UI updates: Context changes visible in browser

---

## 📝 When Starting New Session

1. Read `devProgress.md` first - know current status
2. Pick feature from "Planned" or fix from "Broken"
3. Move to "In Progress"
4. Implement & test
5. Move to "Done (AI)" when complete
6. Ask human to test
7. Human moves to "Done (Tested)" or "Broken"

---

## 🆘 Need More Info?

- **Architecture details:** `docs/TECHNICAL_SPEC.md`
- **Hardware specs:** `docs/TECHNICAL_SPEC.md` → Hardware section
- **Plugin system:** `docs/TECHNICAL_SPEC.md` → Plugin System section
- **Zero-setup control:** `docs/TECHNICAL_SPEC.md` → Zero-Setup Device Control

---

## 💡 Development Philosophy

- **Modularity** - Components work independently
- **Test-driven** - Nothing done until human verifies
- **Flexible** - User may pivot based on interest
- **Documented** - Future Claude instances should understand code

---

**Ready to build!** Check `devProgress.md` and pick a feature to implement. 🚀
