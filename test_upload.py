import tempfile
from pathlib import Path
import requests
from PIL import Image

BASE = 'http://127.0.0.1:5000'

print('Health:', requests.get(f'{BASE}/health', timeout=5).status_code)

# Try to download a sample food image first
urls = [
    'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=640&q=80',
    'https://images.pexels.com/photos/461198/pexels-photo-461198.jpeg?auto=compress&cs=tinysrgb&w=640'
]

image_path = None
for url in urls:
    try:
        print('Downloading', url)
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        image_path = Path(tempfile.gettempdir()) / 'sample_food.jpg'
        image_path.write_bytes(resp.content)
        break
    except Exception as e:
        print('Download failed:', e)

if image_path is None:
    print('No internet sample; creating a local test image')
    image_path = Path(tempfile.gettempdir()) / 'sample_food.png'
    img = Image.new('RGB', (640, 480), color=(255, 220, 180))
    img.save(image_path)

print('Using image:', image_path)
with image_path.open('rb') as f:
    r = requests.post(f'{BASE}/analyze', files={'image': f}, timeout=180)

print('Status code:', r.status_code)
try:
    print('Response JSON:', r.json())
except Exception:
    print('Response text:', r.text)
