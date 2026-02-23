from PIL import Image
import os

def split_image(image_path, output_dir):
    img = Image.open(image_path)
    width, height = img.size
    
    # Calculate grid size
    grid_w = width // 3
    grid_h = height // 3
    
    os.makedirs(output_dir, exist_ok=True)
    
    count = 1
    for row in range(3):
        for col in range(3):
            left = col * grid_w
            top = row * grid_h
            right = (col + 1) * grid_w
            bottom = (row + 1) * grid_h
            
            # Crop the piece
            piece = img.crop((left, top, right, bottom))
            filename = f"cp-{count:02d}.png"
            output_path = os.path.join(output_dir, filename)
            piece.save(output_path, "PNG")
            print(f"Saved {output_path}")
            count += 1

if __name__ == "__main__":
    source_image = "grid_source.jpg"
    target_dir = "/Users/hipoglisemi/Desktop/kartavantaj/public/placeholders"
    
    if os.path.exists(source_image):
        split_image(source_image, target_dir)
        print("✅ Grid split completed.")
    else:
        print(f"❌ Source image {source_image} not found.")
