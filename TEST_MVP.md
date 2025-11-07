# 🧪 Donk MVP Testing Guide

## ✅ What's Ready

The MVP is complete with:
- HQ Pi Flask server with WebSocket hub
- Collector agent with auto-reconnect
- Web UI showing connected collectors
- All dependencies installed

---

## 🚀 How to Test

### Terminal 1: Start HQ Pi Server

```bash
cd ~/donk-project/hq-pi
source venv/bin/activate
python flask_app/main.py
```

**Expected output:**
```
============================================================
Donk HQ Pi Server Starting
============================================================
Listening on: http://0.0.0.0:5000
Tailscale IP: http://100.74.135.15:5000
Press Ctrl+C to stop
============================================================
```

### Terminal 2: Start Collector (on HQ Pi for testing)

```bash
cd ~/donk-project/collector
source venv/bin/activate
python collector.py
```

**Expected output:**
```
============================================================
Donk Collector Agent Starting
============================================================
Device ID: floopatron-linux
Hostname: floopatron
Platform: Linux
HQ Pi URL: http://100.74.135.15:5000
============================================================
Connecting to HQ Pi...
Connection established!
Registration acknowledged by HQ Pi
Collector agent running. Press Ctrl+C to stop.
```

### Browser: View Web UI

**Option 1: From same machine (HQ Pi)**
```
http://localhost:5000
```

**Option 2: From Tailscale device (laptop, phone)**
```
http://100.74.135.15:5000
```

**Option 3: From same WiFi network**
```
http://192.168.1.73:5000
```

**Expected result:**
- Web page loads with purple gradient header
- "Connected Collectors" shows 1
- Collector card appears showing:
  - Hostname: floopatron
  - Device ID: floopatron-linux
  - Platform: Linux
  - Connected time

---

## 📝 Test Checklist

- [ ] HQ Pi server starts without errors
- [ ] Collector connects to HQ Pi
- [ ] Collector receives registration acknowledgment
- [ ] Web UI loads in browser
- [ ] WebSocket status shows "Connected" (green dot)
- [ ] Collector count shows "1"
- [ ] Collector card appears with correct info
- [ ] Stop collector (Ctrl+C) → count updates to 0
- [ ] Restart collector → reconnects automatically
- [ ] Open web UI from phone/laptop → works via Tailscale

---

## 🎯 Next Steps After Testing

Once MVP is verified working:

1. **Pull to laptop:**
   ```bash
   # On laptop (via git clone or pull)
   cd ~/donk-project/collector
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python collector.py
   ```

2. **See 2 collectors connected:**
   - HQ Pi collector (floopatron-linux)
   - Laptop collector (your-laptop-name)

3. **Mark MVP as tested in devProgress.md**

4. **Move on to Phase 1 features:**
   - System monitor plugin
   - Plugin loader
   - Context updates

---

## 🐛 Troubleshooting

**Collector can't connect:**
- Check HQ Pi server is running
- Verify Tailscale is running: `sudo tailscale status`
- Try local URL: `python collector.py --hq-url http://localhost:5000`

**Web UI not loading:**
- Check firewall allows port 5000
- Try accessing from same machine first: `http://localhost:5000`

**Permission errors:**
- Make sure you activated the venv: `source venv/bin/activate`

---

**Ready to test!** Start with Terminal 1 (HQ Pi server), then Terminal 2 (collector), then open browser. 🚀
