from PIL import Image, ImageDraw

# Create a new image with a white background
size = (256, 256)
image = Image.new('RGBA', size, (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Draw a folder shape
folder_color = (52, 152, 219)  # Blue
arrow_color = (46, 204, 113)   # Green

# Folder base
draw.rectangle([40, 80, 216, 200], fill=folder_color)
# Folder tab
draw.rectangle([40, 60, 120, 80], fill=folder_color)

# Arrow
arrow_points = [
    (80, 140),   # Left point
    (128, 100),  # Top point
    (176, 140),  # Right point
    (152, 140),  # Right indent
    (152, 170),  # Bottom right
    (104, 170),  # Bottom left
    (104, 140),  # Left indent
]
draw.polygon(arrow_points, fill=arrow_color)

# Save as ICO
image.save('app_icon.ico', format='ICO', sizes=[(256, 256)])
