import cv2  # type: ignore
import numpy as np
import time
import os
import sys
import datetime
import math
import random
from collections import deque
WINDOW_TITLE        = "Magic Karpet - Invisibility Simulator"
DEFAULT_WIDTH       = 640
DEFAULT_HEIGHT      = 480
BG_CAPTURE_FRAMES   = 30
GHOST_TRAIL_DEPTH   = 8
SCREENSHOT_DIR      = "magic_karpet_screenshots"
COLOR_PROFILES = {
    "red": {
        "name":        "Red",
        "emoji":       "[RED]",
        "ranges": [
            ((0,   80, 60),  (10,  255, 255)),
            ((165, 80, 60),  (179, 255, 255)),
        ],
        "hud_color":   (0, 0, 255),
        "sensitivity": 15,
    },
    "green": {
        "name":        "Green",
        "emoji":       "[GRN]",
        "ranges": [
            ((36, 80, 60), (86, 255, 255)),
        ],
        "hud_color":   (0, 200, 0),
        "sensitivity": 15,
    },
    "blue": {
        "name":        "Blue",
        "emoji":       "[BLU]",
        "ranges": [
            ((94, 80, 60), (130, 255, 255)),
        ],
        "hud_color":   (255, 100, 0),
        "sensitivity": 15,
    },
    "yellow": {
        "name":        "Yellow",
        "emoji":       "[YLW]",
        "ranges": [
            ((20, 80, 60), (35, 255, 255)),
        ],
        "hud_color":   (0, 220, 220),
        "sensitivity": 10,
    },
    "purple": {
        "name":        "Purple",
        "emoji":       "[PRP]",
        "ranges": [
            ((130, 60, 60), (160, 255, 255)),
        ],
        "hud_color":   (200, 0, 200),
        "sensitivity": 12,
    },
    "orange": {
        "name":        "Orange",
        "emoji":       "[ORG]",
        "ranges": [
            ((10, 80, 60), (25, 255, 255)),
        ],
        "hud_color":   (0, 120, 255),
        "sensitivity": 12,
    },
}

COLOR_CYCLE = ["red", "green", "blue", "yellow", "purple", "orange"]

PRESETS = {
    1: {"name": "Classic",  "edge": False, "ghost": False, "glitch": False, "thermal": False, "night": False},
    2: {"name": "Phantom",  "edge": True,  "ghost": True,  "glitch": False, "thermal": False, "night": False},
    3: {"name": "Glitch",   "edge": False, "ghost": False, "glitch": True,  "thermal": False, "night": False},
    4: {"name": "Thermal",  "edge": False, "ghost": False, "glitch": False, "thermal": True,  "night": False},
    5: {"name": "NightVis", "edge": False, "ghost": False, "glitch": False, "thermal": False, "night": True},
}


def ensure_screenshot_dir():
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
        print(f"[INFO] Created screenshot directory: '{SCREENSHOT_DIR}'")


def timestamp_string():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))


def draw_rounded_rect(img, x1, y1, x2, y2, radius, color, thickness=-1, alpha=1.0):
    h, w = img.shape[:2]
    x1 = int(clamp(x1, 0, w - 1))
    y1 = int(clamp(y1, 0, h - 1))
    x2 = int(clamp(x2, 0, w - 1))
    y2 = int(clamp(y2, 0, h - 1))
    radius = int(clamp(radius, 0, min((x2 - x1) // 2, (y2 - y1) // 2)))

    if thickness == -1:
        overlay = img.copy()
        if x1 + radius < x2 - radius:
            cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        if y1 + radius < y2 - radius:
            cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, -1)
        cv2.circle(overlay, (x1 + radius, y1 + radius), radius, color, -1)
        cv2.circle(overlay, (x2 - radius, y1 + radius), radius, color, -1) 
        cv2.circle(overlay, (x1 + radius, y2 - radius), radius, color, -1)
        cv2.circle(overlay, (x2 - radius, y2 - radius), radius, color, -1)
        cv2.addWeighted(overlay, alpha, img, 1.0 - alpha, 0, img)
    else:
        if x1 + radius < x2 - radius:
            cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
        if y1 + radius < y2 - radius:
            cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, thickness)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, thickness)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, thickness)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, thickness)


def resize_frame(frame, width, height):
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)


def safe_open_camera(camera_index=0, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    print(f"[INFO] Attempting to open camera index {camera_index} ...")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("[ERROR] Could not open webcam!")
        print("        Make sure your webcam is connected and not in use by another app.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Camera opened: resolution {actual_w}x{actual_h}")
    return cap


def capture_background(cap, num_frames=BG_CAPTURE_FRAMES):
    print(f"\n[BG] Capturing background over {num_frames} frames ...")
    print("[BG] Make sure the COLORED CLOTH is NOT in view!")

    countdown_window = "Background Capture"
    cv2.namedWindow(countdown_window, cv2.WINDOW_NORMAL)

    bg_accumulator = None

    for i in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Failed to read frame during background capture.")
            continue

        frame = cv2.flip(frame, 1)

        if bg_accumulator is None:
            bg_accumulator = np.float64(frame)
        else:
            bg_accumulator += frame.astype(np.float64)
        progress_frame = frame.copy()
        pct    = int((i + 1) / num_frames * 100)
        bar_w  = int(frame.shape[1] * pct / 100)
        h_f    = frame.shape[0]
        w_f    = frame.shape[1]

        cv2.rectangle(progress_frame, (0, h_f - 30), (w_f, h_f), (30, 30, 30), -1)
        cv2.rectangle(progress_frame, (0, h_f - 30), (bar_w, h_f), (0, 220, 100), -1)
        cv2.putText(progress_frame, f"Capturing Background: {pct}%",
                    (10, h_f - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(progress_frame, "Keep the cloth OUT of frame!",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)

        cv2.imshow(countdown_window, progress_frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            print("[INFO] Background capture cancelled.")
            cv2.destroyWindow(countdown_window)
            sys.exit(0)

    cv2.destroyWindow(countdown_window)

    if bg_accumulator is None:
        print("[ERROR] No frames captured for background!")
        sys.exit(1)

    background = bg_accumulator / num_frames
    print("[BG] Background captured successfully!\n")
    return background


def build_color_mask(frame_hsv, color_key, sensitivity_offset=0):
    profile  = COLOR_PROFILES[color_key]
    combined = None
    offset   = sensitivity_offset

    for (lo, hi) in profile["ranges"]:
        lo_adj = (
            clamp(lo[0] - offset, 0, 179),
            clamp(lo[1] - 20,     0, 255),
            clamp(lo[2] - 20,     0, 255),
        )
        hi_adj = (
            clamp(hi[0] + offset, 0, 179),
            clamp(hi[1],          0, 255),
            clamp(hi[2],          0, 255),
        )
        part = cv2.inRange(frame_hsv,
                           np.array(lo_adj, dtype=np.uint8),
                           np.array(hi_adj, dtype=np.uint8))
        combined = part if combined is None else cv2.bitwise_or(combined, part)

    k_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN,  k_small)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_large)
    combined = cv2.dilate(combined, k_small, iterations=2)
    return combined


def refine_mask_with_contours(mask, min_area=500):
    refined  = np.zeros_like(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(refined, [c], -1, 255, thickness=cv2.FILLED)
    return refined


def smooth_mask_edges(mask, blur_radius=21):
    if blur_radius % 2 == 0:
        blur_radius += 1
    blurred = cv2.GaussianBlur(mask.astype(np.float32),
                                (blur_radius, blur_radius), 0)
    return blurred / 255.0


def apply_invisibility(frame, background, soft_mask):
    alpha   = soft_mask[:, :, np.newaxis]
    frame_f = frame.astype(np.float32)
    bg_f    = background.astype(np.float32)
    result  = bg_f * alpha + frame_f * (1.0 - alpha)
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_ghost_trail(current_frame, trail_buffer, mask):
    if len(trail_buffer) == 0:
        return current_frame

    depth  = len(trail_buffer)
    raw_w  = [0.5 ** (depth - i) for i in range(depth)]
    total  = sum(raw_w)
    weights = [w / total for w in raw_w]

    ghost = np.zeros_like(current_frame, dtype=np.float32)
    for idx, f in enumerate(trail_buffer):
        ghost += f.astype(np.float32) * weights[idx]
    ghost = np.clip(ghost, 0, 255).astype(np.uint8)

    mask_bool = mask > 127
    result    = current_frame.copy()
    if mask_bool.any():
        result[mask_bool] = cv2.addWeighted(
            current_frame, 0.3, ghost, 0.7, 0)[mask_bool]
    return result


def apply_edge_detection(frame, mask):
    result      = frame.copy()
    region      = cv2.bitwise_and(frame, frame, mask=mask)
    gray        = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    edges       = cv2.Canny(gray, 50, 150)
    e_kernel    = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    edges       = cv2.dilate(edges, e_kernel, iterations=1)
    edge_color  = np.zeros_like(frame)
    edge_color[edges > 0] = (255, 230, 0)
    return cv2.addWeighted(result, 1.0, edge_color, 0.8, 0)


def apply_glitch_effect(frame, intensity=0.05):
    glitched = frame.copy()
    h, w     = frame.shape[:2]
    num_rows = max(1, min(int(h * intensity), h))
    rows     = random.sample(range(h), num_rows)

    for row in rows:
        shift = random.randint(-30, 30)
        if shift == 0:
            continue
        if shift > 0:
            glitched[row, shift:, :]  = frame[row, :-shift, :]
            glitched[row, :shift, :]  = frame[row, -shift:, :]
        else:
            s = abs(shift)
            glitched[row, :w - s, :]  = frame[row, s:, :]
            glitched[row, w - s:, :]  = frame[row, :s, :]

    if random.random() < 0.15:
        offset = random.randint(2, 6)
        if offset < w:
            glitched[:, offset:, 0] = frame[:, :-offset, 0]

    return glitched


def apply_thermal_vision(frame):
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    thermal = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
    return thermal


def apply_night_vision(frame):
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    boosted = cv2.convertScaleAbs(gray, alpha=1.8, beta=30)
    night   = np.zeros_like(frame)
    night[:, :, 1] = boosted

    night[::4, :, :] = (night[::4, :, :] * 0.6).astype(np.uint8)

    h, w   = frame.shape[:2]
    cx, cy = w // 2, h // 2
    Y, X   = np.ogrid[:h, :w]
    dist   = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_d  = np.sqrt(cx ** 2 + cy ** 2)
    vig    = np.clip(1.0 - (dist / max_d) ** 1.5, 0, 1)[:, :, np.newaxis]
    return (night.astype(np.float32) * vig).astype(np.uint8)


def apply_scanline_overlay(frame, line_spacing=3, alpha=0.12):
    out = frame.copy()
    out[::line_spacing, :, :] = (
        out[::line_spacing, :, :] * (1.0 - alpha)
    ).astype(np.uint8)
    return out


def apply_vignette(frame, strength=0.5):
    h, w   = frame.shape[:2]
    cx, cy = w // 2, h // 2
    Y, X   = np.ogrid[:h, :w]
    dist   = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    vig    = np.clip(1.0 - dist * strength, 0, 1)[:, :, np.newaxis]
    return (frame.astype(np.float32) * vig).astype(np.uint8)


def apply_cloth_shimmer(frame, mask, frame_count):
    result  = frame.copy()
    k       = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    border  = cv2.dilate(mask, k) - cv2.erode(mask, k)
    pulse   = (math.sin(frame_count * 0.15) + 1.0) / 2.0
    si      = 0.4 + 0.6 * pulse

    shimmer = np.array(
        [int(200 * si), int(255 * si), int(200 * si)], dtype=np.uint8
    )
    border_px = border > 0
    count_bp  = int(border_px.sum())

    if count_bp > 0:
        region   = result[border_px].reshape(-1, 3)
        shimmer_tile = np.tile(shimmer, (count_bp, 1)).reshape(-1, 3)
        blended  = cv2.addWeighted(region, 0.3, shimmer_tile, 0.7, 0)
        result[border_px] = blended.reshape(-1, 3)

    return result


def apply_portal_effect(frame, mask, frame_count):
    result     = frame.copy()
    cloth_rows = np.where(mask > 127)

    if len(cloth_rows[0]) == 0:
        return result

    cy = int(np.mean(cloth_rows[0]))
    cx = int(np.mean(cloth_rows[1]))

    for i in range(5):
        phase  = (frame_count * 3 + i * 18) % 360
        radius = int(20 + i * 15 + 8 * math.sin(math.radians(phase)))
        a_val  = 0.3 + 0.7 * abs(math.sin(math.radians(phase)))
        color  = (
            int(100 * a_val),
            int(200 * a_val),
            int(255 * a_val),
        )
        if radius > 0:
            cv2.circle(result, (cx, cy), radius, color, 1, cv2.LINE_AA)

    cv2.circle(result, (cx, cy), 4, (255, 255, 255), -1, cv2.LINE_AA)
    return result


def draw_hud(frame, state):
    result = frame.copy()
    h, w   = result.shape[:2]

    panel_w, panel_h = 270, 225
    draw_rounded_rect(result, 8, 8, panel_w, panel_h, 10,
                      (10, 10, 10), thickness=-1, alpha=0.65)
    draw_rounded_rect(result, 8, 8, panel_w, panel_h, 10,
                      state["color_profile"]["hud_color"], thickness=1)

    cv2.putText(result, "MAGIC KARPET",
                (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2)

    fps_color = (0, 255, 0) if state["fps"] >= 20 else (0, 100, 255)
    cv2.putText(result, f"FPS: {state['fps']:.1f}",
                (18, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.5, fps_color, 1)

    cp = state["color_profile"]
    cv2.putText(result, f"Color: {cp['emoji']} {cp['name']}",
                (18, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cp["hud_color"], 1)

    cv2.putText(result, f"Sensitivity: {state['sensitivity_offset']:+d}",
                (18, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cov     = state.get("coverage_pct", 0.0)
    bar_max = 200
    filled  = int(bar_max * min(cov / 100.0, 1.0))
    cv2.rectangle(result, (18, 110), (18 + bar_max, 124), (50, 50, 50), -1)
    cv2.rectangle(result, (18, 110), (18 + filled,  124), (0, 200, 100), -1)
    cv2.putText(result, f"Coverage: {cov:.1f}%",
                (18, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    effects = "Effects: "
    if state["effect_edge"]:    effects += "Edge "
    if state["effect_ghost"]:   effects += "Ghost "
    if state["effect_glitch"]:  effects += "Glitch "
    if state["effect_thermal"]: effects += "Thermal "
    if state["effect_night"]:   effects += "Night "
    if effects == "Effects: ":  effects += "None"
    cv2.putText(result, effects,
                (18, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 180, 100), 1)

    cv2.putText(result, f"Preset: {state.get('preset_name', 'Custom')}",
                (18, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 255, 180), 1)

    bg_ok    = state["bg_captured"]
    bg_text  = "BG: Captured" if bg_ok else "BG: NOT CAPTURED"
    bg_color = (0, 220, 0) if bg_ok else (0, 0, 255)
    cv2.putText(result, bg_text,
                (18, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.45, bg_color, 1)

    keys = [
        "Q:Quit", "SPACE:RecapBG", "S:Screenshot", "M:Color",
        "E:Edge", "G:Ghost", "X:Glitch", "T:Thermal", "N:Night",
        "D:Debug", "+/-:Sensitivity", "1-5:Presets", "R:Reset"
    ]
    bar_y = h - 25
    cv2.rectangle(result, (0, bar_y - 4), (w, h), (15, 15, 15), -1)

    key_x = 6
    for k in keys:
        sz, _ = cv2.getTextSize(k, cv2.FONT_HERSHEY_SIMPLEX, 0.36, 1)
        if key_x + sz[0] + 12 > w:
            break
        cv2.putText(result, k, (key_x, bar_y + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 220, 255), 1)
        key_x += sz[0] + 14

    ts      = datetime.datetime.now().strftime("%H:%M:%S")
    ts_sz, _= cv2.getTextSize(ts, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.putText(result, ts, (w - ts_sz[0] - 10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    return result


def draw_debug_mask(frame, mask, background):
    h, w    = frame.shape[:2]
    half_w  = w // 2

    left    = resize_frame(frame, half_w, h)
    right   = resize_frame(background.astype(np.uint8), half_w, h)

    msk_r   = cv2.resize(mask, (half_w, h))
    blend   = (left.astype(np.float32) * 0.4 +
               np.array([0, 0, 200], dtype=np.float32) * 0.6)
    left[msk_r > 127] = np.clip(blend, 0, 255).astype(np.uint8)[msk_r > 127]

    cv2.putText(left,  "LIVE + MASK (red)",
                (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    cv2.putText(right, "BACKGROUND",
                (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)

    debug = np.hstack([left, right])
    cv2.line(debug, (half_w, 0), (half_w, h), (255, 255, 255), 2)
    return debug


class FPSTracker:
    def __init__(self, window_size=30):
        self.timestamps = deque(maxlen=window_size)

    def tick(self):
        self.timestamps.append(time.perf_counter())
        if len(self.timestamps) < 2:
            return 0.0
        elapsed = self.timestamps[-1] - self.timestamps[0]
        return (len(self.timestamps) - 1) / elapsed if elapsed > 0 else 0.0


def save_screenshot(frame, prefix="magic_karpet"):
    ensure_screenshot_dir()
    filename = f"{prefix}_{timestamp_string()}.jpg"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    ok = cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if ok:
        print(f"[SCREENSHOT] Saved: {filepath}")
        return filepath
    print(f"[ERROR] Failed to save screenshot: {filepath}")
    return None


def draw_screenshot_flash(frame, duration_frames, current_in_flash):
    if current_in_flash >= duration_frames:
        return frame
    alpha = 1.0 - (current_in_flash / duration_frames)
    flash = np.full_like(frame, 255)
    return cv2.addWeighted(frame, 1.0 - alpha * 0.8, flash, alpha * 0.8, 0)


def handle_keypress(key, state, cap):
    if key == -1 or key == 255:
        return True

    char = chr(key & 0xFF).lower()

    if char == 'q':
        print("[INFO] Quitting...")
        return False

    elif key == 32:
        print("[INFO] Re-capturing background...")
        bg = capture_background(cap, BG_CAPTURE_FRAMES)
        state["background"]  = bg.astype(np.uint8)
        state["bg_captured"] = True
        state["flash_counter"] = 0

    elif char == 's':
        if state.get("last_frame") is not None:
            save_screenshot(state["last_frame"])
            state["flash_counter"] = 0

    elif char == 'e':
        state["effect_edge"] = not state["effect_edge"]
        print(f"[EFFECT] Edge: {'ON' if state['effect_edge'] else 'OFF'}")

    elif char == 'g':
        state["effect_ghost"] = not state["effect_ghost"]
        print(f"[EFFECT] Ghost trail: {'ON' if state['effect_ghost'] else 'OFF'}")

    elif char == 'x':
        state["effect_glitch"] = not state["effect_glitch"]
        print(f"[EFFECT] Glitch: {'ON' if state['effect_glitch'] else 'OFF'}")

    elif char == 'h':
        state["show_hud"] = not state["show_hud"]
        print(f"[HUD] {'ON' if state['show_hud'] else 'OFF'}")

    elif char == 'm':
        idx = COLOR_CYCLE.index(state["color_key"])
        state["color_key"]     = COLOR_CYCLE[(idx + 1) % len(COLOR_CYCLE)]
        state["color_profile"] = COLOR_PROFILES[state["color_key"]]
        state["sensitivity_offset"] = 0
        print(f"[COLOR] Switched to: {state['color_profile']['name']}")

    elif char in ('+', '='):
        state["sensitivity_offset"] = clamp(state["sensitivity_offset"] + 3, -20, 40)
        print(f"[SENSITIVITY] {state['sensitivity_offset']:+d}")

    elif char == '-':
        state["sensitivity_offset"] = clamp(state["sensitivity_offset"] - 3, -20, 40)
        print(f"[SENSITIVITY] {state['sensitivity_offset']:+d}")

    elif char == 'd':
        state["debug_mode"] = not state["debug_mode"]
        print(f"[DEBUG] Mask view: {'ON' if state['debug_mode'] else 'OFF'}")

    elif char == 'f':
        state["fullscreen"] = not state["fullscreen"]
        flag = cv2.WINDOW_FULLSCREEN if state["fullscreen"] else cv2.WINDOW_NORMAL
        cv2.setWindowProperty(WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN, flag)
        print(f"[WINDOW] Fullscreen: {'ON' if state['fullscreen'] else 'OFF'}")

    elif char == 'r':
        state.update({
            "effect_edge": False, "effect_ghost": False,
            "effect_glitch": False, "effect_thermal": False,
            "effect_night": False, "sensitivity_offset": 0,
            "preset_name": "Custom"
        })
        state["ghost_buffer"].clear()
        print("[RESET] All effects reset.")

    elif char == 't':
        state["effect_thermal"] = not state["effect_thermal"]
        if state["effect_thermal"]:
            state["effect_night"] = False
        print(f"[EFFECT] Thermal: {'ON' if state['effect_thermal'] else 'OFF'}")

    elif char == 'n':
        state["effect_night"] = not state["effect_night"]
        if state["effect_night"]:
            state["effect_thermal"] = False
        print(f"[EFFECT] Night vision: {'ON' if state['effect_night'] else 'OFF'}")

    elif char in ('1', '2', '3', '4', '5'):
        p_num = int(char)
        if p_num in PRESETS:
            p = PRESETS[p_num]
            state.update({
                "effect_edge":    p["edge"],
                "effect_ghost":   p["ghost"],
                "effect_glitch":  p["glitch"],
                "effect_thermal": p["thermal"],
                "effect_night":   p["night"],
                "preset_name":    p["name"],
            })
            print(f"[PRESET] Activated: {p['name']}")

    return True


def compute_coverage(mask):
    total = mask.size
    cloth = int(np.sum(mask > 127))
    return (cloth / total) * 100.0


def draw_stats_panel(frame, history, panel_x, panel_y):
    result   = frame.copy()
    pw, ph   = 140, 60
    px2, py2 = panel_x + pw, panel_y + ph
    draw_rounded_rect(result, panel_x, panel_y, px2, py2,
                      6, (10, 10, 10), -1, alpha=0.65)

    if len(history) < 2:
        return result

    hist_list = list(history)
    max_val   = max(hist_list) if max(hist_list) > 0 else 1.0
    pts = []
    for i, val in enumerate(hist_list):
        x = panel_x + 8 + int(i * (pw - 16) / (len(hist_list) - 1))
        y = panel_y + ph - 12 - int((val / max_val) * (ph - 22))
        pts.append((int(x), int(y)))

    for i in range(len(pts) - 1):
        cv2.line(result, pts[i], pts[i + 1], (0, 200, 100), 1, cv2.LINE_AA)

    cv2.putText(result, f"Coverage: {hist_list[-1]:.1f}%",
                (panel_x + 4, panel_y + ph - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.30, (180, 255, 200), 1)
    return result


def draw_bg_prompt(frame):
    result  = frame.copy()
    h, w    = result.shape[:2]
    overlay = result.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 180), -1)
    cv2.addWeighted(overlay, 0.75, result, 0.25, 0, result)
    msg = "Remove cloth from view, then press SPACE to capture background!"
    sz, _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
    cv2.putText(result, msg, ((w - sz[0]) // 2, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
    return result


def process_frame(raw_frame, state):
    frame = cv2.flip(raw_frame, 1)
    state["ghost_buffer"].append(frame.copy())

    if not state["bg_captured"]:
        out = draw_bg_prompt(frame)
        if state["show_hud"]:
            out = draw_hud(out, state)
        return out

    background = state["background"]
    hsv        = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    raw_mask   = build_color_mask(hsv, state["color_key"], state["sensitivity_offset"])
    clean_mask = refine_mask_with_contours(raw_mask, min_area=300)
    soft_mask  = smooth_mask_edges(clean_mask, blur_radius=25)

    coverage   = compute_coverage(clean_mask)
    state["coverage_pct"] = coverage
    state["coverage_history"].append(coverage)

    output = apply_invisibility(frame, background, soft_mask)

    if state["effect_ghost"] and len(state["ghost_buffer"]) > 2:
        output = apply_ghost_trail(output, state["ghost_buffer"], clean_mask)

    output = apply_cloth_shimmer(output, clean_mask, state["frame_count"])

    if coverage > 1.0:
        output = apply_portal_effect(output, clean_mask, state["frame_count"])

    if state["effect_edge"]:
        output = apply_edge_detection(output, clean_mask)

    if state["effect_glitch"]:
        output = apply_glitch_effect(output, intensity=0.04)

    if state["effect_thermal"]:
        output = apply_thermal_vision(output)
    elif state["effect_night"]:
        output = apply_night_vision(output)

    output = apply_scanline_overlay(output, line_spacing=3, alpha=0.06)
    output = apply_vignette(output, strength=0.35)

    if state["show_hud"]:
        h_out, w_out = output.shape[:2]
        output = draw_stats_panel(output, state["coverage_history"],
                                  w_out - 155, h_out - 75)
        output = draw_hud(output, state)

    if state["debug_mode"]:
        output = draw_debug_mask(frame, clean_mask, background)

    flash_dur = 8
    if state["flash_counter"] < flash_dur:
        output = draw_screenshot_flash(output, flash_dur, state["flash_counter"])
        state["flash_counter"] += 1

    return output


def create_initial_state():
    key = "red"
    return {
        "background":          None,
        "bg_captured":         False,
        "color_key":           key,
        "color_profile":       COLOR_PROFILES[key],
        "sensitivity_offset":  0,
        "effect_edge":         False,
        "effect_ghost":        False,
        "effect_glitch":       False,
        "effect_thermal":      False,
        "effect_night":        False,
        "ghost_buffer":        deque(maxlen=GHOST_TRAIL_DEPTH),
        "show_hud":            True,
        "debug_mode":          False,
        "fullscreen":          False,
        "fps":                 0.0,
        "coverage_pct":        0.0,
        "coverage_history":    deque(maxlen=80),
        "frame_count":         0,
        "last_frame":          None,
        "flash_counter":       999,
        "preset_name":         "Custom",
    }


def show_splash_screen(cap, duration_seconds=3.0):
    print("[INFO] Showing splash screen...")
    start = time.perf_counter()
    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame   = cv2.flip(frame, 1)
        h, w    = frame.shape[:2]
        elapsed = time.perf_counter() - start
        progress = min(elapsed / duration_seconds, 1.0)
        if elapsed >= duration_seconds:
            break

        dark       = (frame * 0.35).astype(np.uint8)
        pulse      = 1.0 + 0.05 * math.sin(elapsed * 4)
        font_scale = 1.6 * pulse

        title = "MAGIC KARPET"
        sub   = "Invisibility Simulator"
        inst  = "Point camera at cloth and press SPACE to begin!"

        t_sz, _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, font_scale, 3)
        s_sz, _ = cv2.getTextSize(sub,   cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        i_sz, _ = cv2.getTextSize(inst,  cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cx, cy  = w // 2, h // 2

        cv2.putText(dark, title,
                    (cx - t_sz[0] // 2, cy - 30),
                    cv2.FONT_HERSHEY_DUPLEX, font_scale, (0, 220, 255), 3, cv2.LINE_AA)
        cv2.putText(dark, sub,
                    (cx - s_sz[0] // 2, cy + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 255, 200), 2, cv2.LINE_AA)
        cv2.putText(dark, inst,
                    (cx - i_sz[0] // 2, cy + 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1, cv2.LINE_AA)

        bw  = int(w * 0.6)
        bx  = (w - bw) // 2
        by  = cy + 80
        cv2.rectangle(dark, (bx, by), (bx + bw, by + 12), (40, 40, 40), -1)
        cv2.rectangle(dark, (bx, by), (bx + int(bw * progress), by + 12), (0, 220, 100), -1)
        cv2.rectangle(dark, (bx, by), (bx + bw, by + 12), (80, 80, 80), 1)
        cv2.putText(dark, "Initializing...",
                    (bx, by - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

        cv2.imshow(WINDOW_TITLE, dark)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    print("[INFO] Splash screen complete.")


def main_loop(cap, state):
    fps_tracker = FPSTracker(window_size=30)
    print("\n" + "=" * 60)
    print("  MAGIC KARPET IS RUNNING!")
    print("=" * 60)
    print("  1. Remove the colored cloth from view.")
    print("  2. Press SPACE to capture the background.")
    print("  3. Hold up the colored cloth it becomes invisible!")
    print("  4. Press H to toggle the HUD overlay.")
    print("  5. Press Q to quit.")
    print("=" * 60 + "\n")

    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    running = True

    while running:
        ret, raw = cap.read()
        if not ret:
            print("[WARNING] Frame read failed. Retrying...")
            time.sleep(0.05)
            continue

        state["fps"]         = fps_tracker.tick()
        state["frame_count"] += 1

        output              = process_frame(raw, state)
        state["last_frame"] = output.copy()

        cv2.imshow(WINDOW_TITLE, output)

        key = cv2.waitKey(1) & 0xFF
        running = handle_keypress(key, state, cap)

        try:
            if cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
                print("[INFO] Window closed by user.")
                running = False
        except cv2.error:
            running = False


def main():
    print("""
==============================================================
          MAGIC KARPET  v2.0
          Computer Vision Invisibility Simulator
==============================================================
    """)

    ensure_screenshot_dir()
    cap   = safe_open_camera(camera_index=0,
                              width=DEFAULT_WIDTH,
                              height=DEFAULT_HEIGHT)
    show_splash_screen(cap, duration_seconds=3.0)
    state = create_initial_state()

    print("\n[INFO] Starting background capture ...")
    print("[INFO] Ensure the COLORED CLOTH is NOT visible in frame.\n")
    bg = capture_background(cap, BG_CAPTURE_FRAMES)
    state["background"]  = bg.astype(np.uint8)
    state["bg_captured"] = True

    try:
        main_loop(cap, state)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by Ctrl+C.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Magic Karpet closed. Goodbye!")


if __name__ == "__main__":
    main()
