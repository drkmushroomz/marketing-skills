"""
Generate a Jetfuel blog featured image matching the site's template style.
- Dark-tinted stock photo background
- Jetfuel Agency logo (extracted from reference)
- Bold centered title text
- Letter-spaced subtitle at bottom

Usage:
    python3 generate_blog_image.py --title "Post Title Here" --subtitle "Subtitle Here" --output image.png
    python3 generate_blog_image.py --title "Post Title Here" --subtitle "Subtitle Here" --bg stock_photo.jpg --output image.png
"""
import argparse
import os
import sys
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np


# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(SCRIPT_DIR, "jf_logo_white2.png")
DEFAULT_BG = os.path.join(SCRIPT_DIR, "stock_bg.jpg")

WIDTH, HEIGHT = 1200, 1200
OVERLAY_OPACITY = 0.78
LOGO_WIDTH = 380


def load_fonts():
    """Load fonts with fallbacks."""
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    font_path_regular = [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    title_font = None
    subtitle_font = None

    for fp in font_paths:
        if os.path.exists(fp):
            title_font = ImageFont.truetype(fp, 82)
            break
    for fp in font_path_regular:
        if os.path.exists(fp):
            subtitle_font = ImageFont.truetype(fp, 28)
            break

    if not title_font:
        title_font = ImageFont.load_default()
    if not subtitle_font:
        subtitle_font = ImageFont.load_default()

    return title_font, subtitle_font


def split_title(title, max_chars_per_line=22):
    """Split title into centered lines."""
    words = title.split()
    lines = []
    current = ""
    for word in words:
        if len(current + " " + word) > max_chars_per_line and current:
            lines.append(current.strip())
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    return lines


def generate_featured_image(title, subtitle="", bg_path=None, output_path="featured.png"):
    """Generate a featured image matching Jetfuel's blog template."""

    # Load or create background
    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert('RGB')
        bg = bg.resize((WIDTH, HEIGHT), Image.LANCZOS)
    elif os.path.exists(DEFAULT_BG):
        bg = Image.open(DEFAULT_BG).convert('RGB')
        bg = bg.resize((WIDTH, HEIGHT), Image.LANCZOS)
    else:
        # Solid dark fallback
        bg = Image.new('RGB', (WIDTH, HEIGHT), (30, 30, 35))

    # Dark overlay
    overlay = Image.new('RGB', (WIDTH, HEIGHT), (20, 20, 24))
    bg = Image.blend(bg, overlay, OVERLAY_OPACITY)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=2))

    # Paste Jetfuel logo
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert('RGBA')
        logo_w = LOGO_WIDTH
        logo_h = int(logo.height * (logo_w / logo.width))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

        logo_x = (WIDTH - logo_w) // 2
        logo_y = 250

        # Create mask from brightness
        logo_arr = np.array(logo.convert('RGB'))
        brightness = np.mean(logo_arr, axis=2)
        mask = Image.fromarray((brightness > 80).astype(np.uint8) * 255).convert('L')
        bg.paste(logo.convert('RGB'), (logo_x, logo_y), mask)

    draw = ImageDraw.Draw(bg)
    title_font, subtitle_font = load_fonts()

    # Draw title
    title_lines = split_title(title)
    line_height = 100
    total_title_height = len(title_lines) * line_height
    y_start = 420

    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        x = (WIDTH - w) // 2
        y = y_start + i * line_height
        # Shadow for readability
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=title_font)
        draw.text((x, y), line, fill='white', font=title_font)

    # Draw subtitle with letter spacing
    if subtitle:
        char_spacing = 6
        total_w = sum(
            draw.textbbox((0, 0), c, font=subtitle_font)[2]
            - draw.textbbox((0, 0), c, font=subtitle_font)[0]
            + char_spacing
            for c in subtitle
        ) - char_spacing

        start_x = (WIDTH - total_w) // 2
        sub_y = 1000

        cx = start_x
        for c in subtitle:
            draw.text((cx + 1, sub_y + 1), c, fill=(0, 0, 0), font=subtitle_font)
            draw.text((cx, sub_y), c, fill=(200, 200, 200), font=subtitle_font)
            bbox = draw.textbbox((0, 0), c, font=subtitle_font)
            cx += (bbox[2] - bbox[0]) + char_spacing

    bg.save(output_path, 'PNG', quality=95)
    print(f"Saved: {output_path} ({os.path.getsize(output_path)} bytes)", file=sys.stderr)
    return output_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Jetfuel blog featured image')
    parser.add_argument('--title', required=True, help='Post title')
    parser.add_argument('--subtitle', default='', help='Subtitle text (letter-spaced at bottom)')
    parser.add_argument('--bg', help='Custom background image path')
    parser.add_argument('--output', default='featured.png', help='Output path')
    args = parser.parse_args()

    generate_featured_image(
        title=args.title,
        subtitle=args.subtitle,
        bg_path=args.bg,
        output_path=args.output,
    )
