import os
import random
import time
import json

import pygame
from PIL import Image, ImageFilter
import cv2

# Load configuration
config_path = "config.json"
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
else:
    raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

# CONFIG
IMAGE_FOLDER = config.get("IMAGE_FOLDER", "/home/max/Downloads/tumblr_backup_062025/media")
DISPLAY_TIME = config.get("DISPLAY_TIME_S", 10)
FADE_TIME = config.get("FADE_TIME_S", 2)
BLUR_RADIUS = config.get("BLUR_RADIUS_PX", 30)
TINT_OPACITY = config.get("TINT_OPACITY", 0.5)


# Helper functions
def resize_to_fit(img):
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
    mode = pil_image.mode
    size = pil_image.size
    data = pil_image.tobytes()
    return pygame.image.fromstring(data, size, mode).convert()


def apply_blur_and_tint(img):
    bg = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    if TINT_OPACITY > 0:
        overlay = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), color=(0, 0, 0))
        bg = Image.blend(bg, overlay, TINT_OPACITY)
    return bg


def load_image_surface(file):
    img = Image.open(file).convert("RGB")
    bg = apply_blur_and_tint(img)
    fg = resize_to_fit(img)
    bg.paste(fg, ((SCREEN_WIDTH - fg.width) // 2, (SCREEN_HEIGHT - fg.height) // 2))
    return pil_to_surface(bg)


def blend_surfaces(surf1, surf2, alpha):
    blended = surf1.copy()
    surf2_alpha = surf2.copy()
    surf2_alpha.set_alpha(int(alpha * 255))
    blended.blit(surf2_alpha, (0, 0))
    return blended


def play_video(file, next_surface=None):
    cap = cv2.VideoCapture(file)
    if not cap.isOpened():
        print(f"Could not open video: {file}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_duration = 1 / fps

    # Read first frame for crossfade
    ret, frame = cap.read()
    if not ret:
        cap.release()
        return

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_frame = Image.fromarray(frame_rgb)
    bg = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), color=(0, 0, 0))
    fg = resize_to_fit(pil_frame)
    bg.paste(fg, ((SCREEN_WIDTH - fg.width) // 2, (SCREEN_HEIGHT - fg.height) // 2))
    current_surface = pil_to_surface(bg)

    # Crossfade in
    fade_start = time.time()
    while time.time() - fade_start < FADE_TIME:
        alpha = (time.time() - fade_start) / FADE_TIME
        if next_surface:
            blended = blend_surfaces(next_surface, current_surface, alpha)
        else:
            blended = current_surface.copy()
            blended.set_alpha(int(alpha * 255))
        screen.blit(blended, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                cap.release()
                pygame.quit()
                exit()

    # Play video frames
    while ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_frame = Image.fromarray(frame_rgb)
        bg = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), color=(0, 0, 0))
        fg = resize_to_fit(pil_frame)
        bg.paste(fg, ((SCREEN_WIDTH - fg.width) // 2, (SCREEN_HEIGHT - fg.height) // 2))
        surface = pil_to_surface(bg)

        screen.blit(surface, (0, 0))
        pygame.display.flip()

        start_time = time.time()
        while time.time() - start_time < frame_duration:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    cap.release()
                    pygame.quit()
                    exit()
            clock.tick(60)
        ret, frame = cap.read()

    cap.release()


def show_slideshow(files):
    while True:
        current_file = random.choice(files)
        ext = os.path.splitext(current_file)[1].lower()

        # Preload next image surface for crossfade if applicable
        next_file = random.choice(files)
        next_ext = os.path.splitext(next_file)[1].lower()
        next_surface = None
        if next_ext not in [".mp4", ".mov", ".avi", ".mkv"]:
            try:
                next_surface = load_image_surface(next_file)
            except:
                next_surface = None

        if ext in [".mp4", ".mov", ".avi", ".mkv"]:
            play_video(current_file, next_surface)
        else:
            try:
                surface = load_image_surface(current_file)
            except:
                continue

            # Crossfade in
            fade_start = time.time()
            while time.time() - fade_start < FADE_TIME:
                alpha = (time.time() - fade_start) / FADE_TIME
                if next_surface:
                    blended = blend_surfaces(next_surface, surface, alpha)
                else:
                    blended = surface.copy()
                    blended.set_alpha(int(alpha * 255))
                screen.blit(blended, (0, 0))
                pygame.display.flip()
                clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()

            # Display for DISPLAY_TIME
            start_time = time.time()
            while time.time() - start_time < DISPLAY_TIME:
                screen.blit(surface, (0, 0))
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()
                clock.tick(60)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    clock = pygame.time.Clock()

    files = [
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".avi", ".mkv"))
    ]

    show_slideshow(files)
