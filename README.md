# 🪄 Magic Karpet — Invisibility Simulator

> **Real-time computer vision invisibility effect using chroma keying, image masking, and live visual effects — all in Python.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv)
![NumPy](https://img.shields.io/badge/NumPy-latest-orange?logo=numpy)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ What Is This?

Magic Karpet is a fun, real-time invisibility simulator inspired by Harry Potter's invisibility cloak. Point your webcam at a **colored cloth**, and it disappears — replaced by the background captured at startup. Layer on effects like ghost trails, glitch, thermal vision, night vision, and more.

**How it works under the hood:**
1. Capture a clean background frame at startup (no cloth in view)
2. Detect a specific color (default: red) in every live frame using HSV masking
3. Replace that colored region with the saved background pixels
4. Optionally apply post-processing effects and a HUD overlay

---

## 🎬 Effects

|--------------------------------------------|---------------------------------------------------------|
|           Effect                           |           Description                                   |
|--------------------------------------------|---------------------------------------------------------|
| Classic Invisibility                       | Colored cloth seamlessly replaced by background         |
| Phantom Mode                               | Ghostly echo trails + edge glow around invisible region |
| Glitch Mode                                | Digital scan-line distortion aesthetic                  |
| Thermal Vision                             | INFERNO colormap overlay (infrared camera sim)          |
| Night Vision                               | Green-tinted NV goggles with scanlines and vignette     |
|--------------------------------------------|---------------------------------------------------------|

---

## 📦 Requirements

- Python **3.8+**
- A working **webcam**
- A **solid-colored cloth** (red works best out of the box)

### Install Dependencies

```bash
pip install opencv-python numpy
```

Or install from a requirements file:

```bash
pip install -r requirements.txt
```

**`requirements.txt`**
```
opencv-python>=4.5.0
numpy>=1.21.0
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/magic-karpet.git
cd magic-karpet
```

### 2. Run the script

```bash
python magic_karpet.py
```

### 3. Follow the on-screen instructions

1. **Remove the colored cloth from your camera's view**
2. The app automatically captures **30 background frames** and averages them into a clean background
3. Once captured, **hold up your colored cloth** — it becomes invisible!
4. Use keyboard controls to tweak effects in real time

> 💡 **Tip:** Consistent lighting dramatically improves the effect. Avoid casting shadows on the cloth.

---

## ⌨️ Controls

| Key | Action |
|-----|--------|
| `Q` | Quit the application |
| `SPACE` | Re-capture background (remove cloth first!) |
| `S` | Save screenshot to `magic_karpet_screenshots/` |
| `M` | Cycle color modes: Red → Green → Blue → Yellow → Purple → Orange |
| `E` | Toggle **edge detection** (cyan force-field glow) |
| `G` | Toggle **ghost trail** effect |
| `X` | Toggle **glitch** effect |
| `T` | Toggle **thermal vision** |
| `N` | Toggle **night vision** |
| `H` | Toggle **HUD** overlay |
| `D` | Toggle **debug mask** view (split-screen) |
| `F` | Toggle **fullscreen** |
| `R` | Reset all effects to defaults |
| `+` / `-` | Increase / decrease color detection sensitivity |
| `1` – `5` | Switch between visual presets |

---

## 🎨 Visual Presets

| Key | Preset | Effects Active |
|-----|--------|----------------|
| `1` | **Classic** | Clean invisibility only |
| `2` | **Phantom** | Edge detection + Ghost trail |
| `3` | **Glitch** | Digital scan-line glitch |
| `4` | **Thermal** | Thermal/infrared colormap |
| `5` | **NightVis** | Night vision goggles simulation |

---

## 🎯 Supported Colors

Press `M` to cycle through:

| Color | Notes |
|-------|-------|
| 🔴 **Red** (default) | Best starting point — most distinct in HSV |
| 🟢 **Green** | Classic chroma key color |
| 🔵 **Blue** | Works well in warm-lit rooms |
| 🟡 **Yellow** | Use in cooler-lit environments |
| 🟣 **Purple** | Good contrast against natural backgrounds |
| 🟠 **Orange** | Strong in daylight settings |

Use `+` / `-` to fine-tune how aggressively the color is detected.

---

## 🛠️ Configuration

You can change defaults at the top of `magic_karpet.py`:

```python
DEFAULT_WIDTH       = 640   # Camera/window width
DEFAULT_HEIGHT      = 480   # Camera/window height
BG_CAPTURE_FRAMES   = 30    # Frames averaged for background
GHOST_TRAIL_DEPTH   = 8     # Number of frames in ghost buffer
SCREENSHOT_DIR      = "magic_karpet_screenshots"  # Output folder
```

### Changing the Default Color

Find `create_initial_state()` and update `"red"` to any key from `COLOR_PROFILES`:

```python
def create_initial_state():
    key = "green"   # change to your cloth color
```

### Adding a Custom Color

Add a new entry to `COLOR_PROFILES`:

```python
"pink": {
    "name":        "Pink",
    "emoji":       "[PNK]",
    "ranges": [
        ((150, 50, 100), (175, 255, 255)),
    ],
    "hud_color":   (200, 100, 200),
    "sensitivity": 12,
},
```

Then add `"pink"` to the `COLOR_CYCLE` list.

> 💡 Use a tool like [HSV Color Picker](https://colorpicker.me/) or OpenCV's HSV output to find the right range for your cloth.

---

## 📸 Screenshots

Press `S` at any time to save a screenshot. Files are saved to `magic_karpet_screenshots/` with timestamps:

```
magic_karpet_screenshots/
  magic_karpet_2025-06-01_14-32-10.jpg
  magic_karpet_2025-06-01_14-35-42.jpg
```

---

## 💡 Tips for Best Results

| Tip | Why It Helps |
|-----|-------------|
| Use a **bright, solid-colored cloth** | Easier to segment cleanly from background |
| **Red or green fabric** works best | Most distinct in HSV color space |
| Keep **lighting consistent** | Fluctuating light causes mask flickering |
| Capture the background **without cloth** in view | The saved background must be cloth-free |
| **Don't wear the same color** as the cloth | You'll partially disappear too! |
| Use a **static camera** (tripod/stand) | Camera movement breaks the illusion |
| Shoot indoors with **diffuse lighting** | Harsh shadows reduce mask quality |
| Press `D` to see the **debug mask** | Helps diagnose detection issues |

---

## 🧰 Project Structure

```
magic-karpet/
├── magic_karpet.py              # Main script — everything in one file
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── magic_karpet_screenshots/    # Auto-created on first screenshot
```

---

## 🔧 Troubleshooting

**Webcam won't open**
- Make sure no other app (Zoom, Teams, OBS) is using the camera
- Try changing `camera_index=0` to `1` or `2` in `safe_open_camera()`

**Effect is patchy or flickering**
- Press `+` to increase detection sensitivity
- Improve lighting — avoid shadows falling on the cloth
- Re-capture the background with `SPACE` after adjusting the scene

**Wrong color being detected**
- Press `M` to cycle to the correct color
- Press `D` (debug view) to see exactly what the mask is detecting
- Use `+`/`-` to adjust sensitivity threshold

**Low FPS / lag**
- Reduce `DEFAULT_WIDTH` and `DEFAULT_HEIGHT` in the config (e.g. to 320×240)
- Disable heavy effects (thermal, night vision)
- Close other CPU-intensive applications

---

## 🤝 Contributing

Pull requests are welcome! Ideas for future improvements:

- [ ] Click-to-pick color from live frame
- [ ] Multi-color cloth support
- [ ] Video recording output
- [ ] Replace background with a custom image or video
- [ ] Depth-aware masking with a stereo/depth camera

---

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

Built with:
- [OpenCV](https://opencv.org/) — computer vision backbone
- [NumPy](https://numpy.org/) — fast array operations
- Inspired by classic chroma key / green screen techniques and, of course, Harry Potter ✨
