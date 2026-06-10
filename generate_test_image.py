#!/usr/bin/env python
"""Generate a random test image of a person"""
import os
from PIL import Image, ImageDraw
import random

# Create image with random colors representing a portrait
width, height = 300, 400
image = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(image)

# Random skin tone (peachy/tan colors)
skin_tones = [(255, 219, 172), (255, 200, 124), (210, 180, 140), (228, 183, 123), (245, 217, 183)]
skin_color = random.choice(skin_tones)

# Random hair color
hair_colors = [(139, 69, 19), (0, 0, 0), (205, 133, 63), (184, 134, 11), (101, 67, 33)]
hair_color = random.choice(hair_colors)

# Random eye color
eye_colors = [(139, 69, 19), (0, 100, 200), (34, 139, 34)]
eye_color = random.choice(eye_colors)

# Draw head/face (circle)
face_x, face_y = 150, 120
face_radius = 70
draw.ellipse([face_x - face_radius, face_y - face_radius, face_x + face_radius, face_y + face_radius], fill=skin_color, outline='black', width=2)

# Draw hair
draw.ellipse([face_x - face_radius, face_y - face_radius - 20, face_x + face_radius, face_y - 10], fill=hair_color, outline='black', width=2)

# Draw eyes
eye_y = face_y - 20
draw.ellipse([face_x - 30, eye_y - 15, face_x - 10, eye_y + 5], fill='white', outline='black', width=1)
draw.ellipse([face_x + 10, eye_y - 15, face_x + 30, eye_y + 5], fill='white', outline='black', width=1)
draw.ellipse([face_x - 22, eye_y - 8, face_x - 18, eye_y - 4], fill=eye_color)
draw.ellipse([face_x + 18, eye_y - 8, face_x + 22, eye_y - 4], fill=eye_color)

# Draw nose
nose_points = [(face_x - 2, face_y - 5), (face_x + 2, face_y - 5), (face_x, face_y + 10)]
draw.polygon(nose_points, fill=skin_color, outline='black')

# Draw mouth
mouth_y = face_y + 30
draw.arc([face_x - 20, mouth_y - 5, face_x + 20, mouth_y + 15], 0, 180, fill='red', width=2)

# Draw body/shoulders
shoulder_y = face_y + face_radius + 10
draw.rectangle([face_x - 60, shoulder_y, face_x + 60, height], fill=random.choice([(100, 100, 150), (150, 100, 100), (100, 150, 100)]), outline='black', width=2)

# Save image
output_dir = os.path.join(os.path.dirname(__file__), 'data', 'uploads', 'team')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'test_person.png')
image.save(output_path)
print(f'✓ Generated test image: {output_path}')
