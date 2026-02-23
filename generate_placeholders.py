import os
import random

COLORS = [
    "#FF5A5F", # Airbnb Red
    "#00A699", # Airbnb Teal
    "#FC642D", # Airbnb Mustard
    "#FF671F", # Chippin Orange
    "#484848", # Dark Grey
    "#767676", # Light Grey
]

BG_COLORS = [
    "#FFF8F6", # Light Red
    "#F0FBFB", # Light Teal
    "#FFF5F0", # Light Mustard
    "#FFF0E6", # Light Orange
    "#F7F7F7", # Light Grey
]

OUTPUT_DIR = "public/placeholders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def random_circle():
    cx = random.randint(0, 400)
    cy = random.randint(0, 250)
    r = random.randint(20, 100)
    color = random.choice(COLORS)
    opacity = random.uniform(0.1, 0.5)
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" fill-opacity="{opacity}" />'

def random_rect():
    x = random.randint(0, 400)
    y = random.randint(0, 250)
    w = random.randint(50, 150)
    h = random.randint(50, 150)
    color = random.choice(COLORS)
    opacity = random.uniform(0.1, 0.5)
    rotation = random.randint(0, 90)
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="{opacity}" transform="rotate({rotation} {x+w/2} {y+h/2})" />'

def generate_svg(index):
    bg_color = random.choice(BG_COLORS)
    shapes = []
    
    # Add random shapes
    for _ in range(random.randint(3, 7)):
        if random.random() > 0.5:
            shapes.append(random_circle())
        else:
            shapes.append(random_rect())
            
    svg_content = f"""<svg width="400" height="250" viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="{bg_color}" />
    {''.join(shapes)}
    <!-- Center Icon or Text (Optional) -->
    <path d="M200,125 m-30,0 a30,30 0 1,0 60,0 a30,30 0 1,0 -60,0" fill="none" stroke="{random.choice(COLORS)}" stroke-width="2" stroke-opacity="0.2"/>
</svg>"""

    filename = f"cp-{index+1:02d}.svg"
    path = os.path.join(OUTPUT_DIR, filename)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"Generated {path}")

def main():
    print("🎨 Generating 20 Vector Graphics...")
    for i in range(20):
        generate_svg(i)
    print("✅ Done.")

if __name__ == "__main__":
    main()
