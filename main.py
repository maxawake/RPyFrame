import json
import os
import random
import threading
import time
from collections import deque

import pygame
from PIL import Image, ImageFilter

# Load configuration from JSON file
config_path = "config.json"
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
else:
    raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

# CONFIG
IMAGE_FOLDER = config.get("IMAGE_FOLDER", "/home/max/media")
DISPLAY_TIME = config.get("DISPLAY_TIME_S", 10)  # seconds per image
FADE_TIME = config.get("FADE_TIME_S", 2)  # seconds for crossfade
BLUR_RADIUS = config.get("BLUR_RADIUS_PX", 30)
TINT_OPACITY = config.get("TINT_OPACITY", 0.5)  # 0.0 (no tint) to 1.0 (fully black)


def resize_to_fit(img):
    """Resize the image to fit the screen while maintaining aspect ratio."""
    img_ratio = img.width / img.height
    screen_ratio = SCREEN_WIDTH / SCREEN_HEIGHT

    if img_ratio > screen_ratio:
        new_width = SCREEN_WIDTH
        new_height = int(SCREEN_WIDTH / img_ratio)
    else:
        new_height = SCREEN_HEIGHT
        new_width = int(SCREEN_HEIGHT * img_ratio)
    return img.resize((new_width, new_height), Image.LANCZOS)


def pil_to_surface(pil_image):
    """Convert a PIL image to a Pygame surface."""
    mode = pil_image.mode
    size = pil_image.size
    data = pil_image.tobytes()
    return pygame.image.fromstring(data, size, mode).convert()


def apply_blur_and_tint(img):
    """Apply Gaussian blur and optional tint to the image."""
    bg = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    if TINT_OPACITY > 0:
        overlay = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), color=(0, 0, 0))
        bg = Image.blend(bg, overlay, TINT_OPACITY)
    return bg


def load_image_data(file):
    """
    Load image data from a file.
    """
    img = Image.open(file)
    frames = []
    durations = []

    try:
        while True:
            frame = img.convert("RGB")
            bg = apply_blur_and_tint(frame)
            fg = resize_to_fit(frame)
            bg.paste(fg, ((SCREEN_WIDTH - fg.width) // 2, (SCREEN_HEIGHT - fg.height) // 2))

            frames.append(bg.copy())
            durations.append(img.info.get("duration", 100) / 1000)
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not durations:
        durations = [DISPLAY_TIME]

    return frames, durations


def blend_surfaces(surf1, surf2, alpha):
    """Blend two surfaces with a given alpha value."""
    blended = surf1.copy()
    surf2_alpha = surf2.copy()
    surf2_alpha.set_alpha(int(alpha * 255))
    blended.blit(surf2_alpha, (0, 0))
    return blended


def preload_worker(q, files):
    """Worker thread to preload images into the queue."""
    while True:
        try:
            file = random.choice(files)
            frames_pil, durations = load_image_data(file)
            q.append((file, frames_pil, durations))
        except Exception as e:
            print(f"Preload error: {e}")


def get_exit_signal():
    """Check for exit signals from the user."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            exit()


def show_slideshow(files):
    q = deque(maxlen=5)  # Preload up to 5 images

    # Start preloading thread
    preload_thread = threading.Thread(target=preload_worker, args=(q, files), daemon=True)
    preload_thread.start()

    # Wait for at least 3 images to be preloaded
    while len(q) < 3:
        time.sleep(1.0)
        print(f"Waiting for preloaded images... {len(q)} loaded")

    file, prev_frames, prev_durations = q.popleft()
    file, next_frames, next_durations = q.popleft()

    prev_frames = [pil_to_surface(frame) for frame in prev_frames]
    next_frames = [pil_to_surface(frame) for frame in next_frames]

    prev_idx = 0
    prev_start = time.time()

    # Main slideshow loop
    while True:
        if time.time() - prev_start >= DISPLAY_TIME:
            fade_start = time.time()
            # Precompute blended surfaces for crossfade
            n = int(10)  # Number of frames for fade at 60 FPS
            blended_frames = []
            for i in range(n):
                alpha = (i + 1) / n
                prev_frame = prev_frames[prev_idx % len(prev_frames)]
                next_frame = next_frames[0]
                blended = blend_surfaces(prev_frame, next_frame, alpha)
                blended_frames.append(blended)

            # Display precomputed blended frames
            for blended in blended_frames:
                screen.blit(blended, (0, 0))
                pygame.display.flip()
                clock.tick(60)
                get_exit_signal()

            # Update to next image
            prev_frames, prev_durations = next_frames, next_durations
            prev_idx = 0
            prev_start = time.time()
            file, next_frames, next_durations = q.popleft()
            next_frames = [pil_to_surface(frame) for frame in next_frames]

        # Display the current frame
        prev_frame = prev_frames[prev_idx % len(prev_frames)]
        screen.blit(prev_frame, (0, 0))
        pygame.display.flip()

        # Handle frame duration
        if len(prev_frames) > 1:
            duration = prev_durations[prev_idx % len(prev_durations)]
            time.sleep(duration)
            prev_idx += 1
        else:
            time.sleep(0.05)

        # Check for exit signal
        get_exit_signal()


if __name__ == "__main__":
    # Pygame init
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    clock = pygame.time.Clock()

    # Get image files
    files = [
        os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    # Start slideshow
    show_slideshow(files)
