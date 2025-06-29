import os
import random
import time
import pygame
from PIL import Image, ImageFilter, ImageEnhance

# CONFIG
IMAGE_FOLDER = "/run/media/max/Externe/New/Bilder/Tumblr/Blogs/spiritual-natura"
DISPLAY_TIME = 10  # seconds per image
FADE_TIME = 2  # seconds for crossfade
BLUR_RADIUS = 30
TINT_OPACITY = 0.5  # 0.0 (no tint) to 1.0 (fully black)

# Pygame init
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
clock = pygame.time.Clock()

# Get image files
files = [
    os.path.join(IMAGE_FOLDER, f)
    for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
]


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


def load_image_data(file):
    img = Image.open(file)
    frames = []
    durations = []

    try:
        while True:
            frame = img.convert("RGB")
            bg = apply_blur_and_tint(frame)
            fg = resize_to_fit(frame)
            bg.paste(fg, ((SCREEN_WIDTH - fg.width) // 2, (SCREEN_HEIGHT - fg.height) // 2))

            surface = pil_to_surface(bg)
            frames.append(surface)
            durations.append(img.info.get("duration", 100) / 1000)
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not durations:
        durations = [DISPLAY_TIME]

    return frames, durations


def blend_surfaces(surf1, surf2, alpha):
    blended = surf1.copy()
    surf2_alpha = surf2.copy()
    surf2_alpha.set_alpha(int(alpha * 255))
    blended.blit(surf2_alpha, (0, 0))
    return blended


def show_slideshow():
    prev_frames, prev_durations = load_image_data(random.choice(files))
    next_frames, next_durations = load_image_data(random.choice(files))

    prev_idx = 0
    prev_start = time.time()

    while True:
        if time.time() - prev_start >= DISPLAY_TIME:
            fade_start = time.time()
            while time.time() - fade_start < FADE_TIME:
                alpha = (time.time() - fade_start) / FADE_TIME
                prev_frame = prev_frames[prev_idx % len(prev_frames)]
                next_frame = next_frames[0]
                blended = blend_surfaces(prev_frame, next_frame, alpha)
                screen.blit(blended, (0, 0))
                pygame.display.flip()
                clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()
            prev_frames, prev_durations = next_frames, next_durations
            prev_idx = 0
            prev_start = time.time()
            next_frames, next_durations = load_image_data(random.choice(files))

        now = time.time()
        prev_frame = prev_frames[prev_idx % len(prev_frames)]
        screen.blit(prev_frame, (0, 0))
        pygame.display.flip()

        if len(prev_frames) > 1:
            duration = prev_durations[prev_idx % len(prev_durations)]
            time.sleep(duration)
            prev_idx += 1
        else:
            time.sleep(0.05)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()


show_slideshow()
