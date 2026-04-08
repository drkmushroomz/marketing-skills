from PIL import Image, ImageDraw, ImageFont
import textwrap

img = Image.new('RGB', (1200, 1200), color=(26, 26, 46))
draw = ImageDraw.Draw(img)

# Gradient-like overlay at top and bottom
for y in range(200):
    alpha = int(30 * (1 - y/200))
    draw.line([(0, y), (1200, y)], fill=(255, 107, 53, alpha))

# Accent bar
draw.rectangle([(80, 80), (120, 140)], fill=(255, 107, 53))
draw.rectangle([(130, 80), (170, 140)], fill=(255, 107, 53))

# "JETFUEL AGENCY" branding at top
try:
    font_brand = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
    font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 68)
    font_sub = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32)
    font_tag = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
except:
    font_brand = ImageFont.load_default()
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_tag = ImageFont.load_default()

# Brand name
brand_text = "JETFUEL AGENCY"
bbox = draw.textbbox((0,0), brand_text, font=font_brand)
bw = bbox[2]-bbox[0]
draw.text(((1200-bw)//2, 90), brand_text, fill=(255, 107, 53), font=font_brand)

# Separator line
draw.rectangle([(100, 145), (1100, 148)], fill=(255, 107, 53))

# Title text
title = "In-House vs Agency Marketing"
subtitle_line1 = "The 2026 Decision Guide"
subtitle_line2 = "for DTC Brands"

# Main title
lines = textwrap.wrap(title, width=22)
y = 320
for line in lines:
    bbox = draw.textbbox((0,0), line, font=font_title)
    w = bbox[2]-bbox[0]
    draw.text(((1200-w)//2, y), line, fill=(255, 255, 255), font=font_title)
    y += 85

# Subtitle
y += 20
for sub in [subtitle_line1, subtitle_line2]:
    bbox = draw.textbbox((0,0), sub, font=font_sub)
    w = bbox[2]-bbox[0]
    draw.text(((1200-w)//2, y), sub, fill=(255, 107, 53), font=font_sub)
    y += 50

# Tag line at bottom
tag = "jetfuel.agency"
bbox = draw.textbbox((0,0), tag, font=font_tag)
tw = bbox[2]-bbox[0]
draw.text(((1200-tw)//2, 1100), tag, fill=(180, 180, 180), font=font_tag)

# Bottom accent
draw.rectangle([(0, 1150), (1200, 1200)], fill=(255, 107, 53))

img.save('featured.png')
print('Featured image saved: featured.png')
