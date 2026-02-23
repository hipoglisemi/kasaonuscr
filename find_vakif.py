
import os

start_path = '/Users/hipoglisemi/Desktop/kartavantaj-scraper/final'
for root, dirs, files in os.walk(start_path):
    for f in files:
        if 'vakif' in f.lower() or 'vakif' in root.lower():
            print(os.path.join(root, f))
