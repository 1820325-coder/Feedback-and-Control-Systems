# 🍳 Recipe Assistant - YOLOv8 + LM Studio Setup

## ✅ Installation Complete!

You've installed all required packages:
- **ultralytics** - YOLOv8 for ingredient detection
- **flask** - Backend server
- **flask-cors** - Cross-origin requests
- **pillow** - Image processing
- **opencv-python** - Computer vision

---

## 🚀 How to Start

### Step 1: Start Your Backend Server
Open PowerShell and run:

```powershell
cd c:\Users\Israel\OneDrive\Desktop\ewan
.\.venv\Scripts\python.exe app.py
```

You'll see:
```
==================================================
🍳 Recipe Assistant Backend Server
==================================================
✓ YOLOv8 loaded for ingredient detection
✓ LM Studio integration ready
✓ Flask server starting on http://127.0.0.1:5000
```

⚠️ **First run will download YOLOv8 model (~35MB)** - be patient!

---

### Step 2: Make Sure LM Studio is Running
- Keep LM Studio running at **http://192.168.55.1:1234**
- Check it has a model loaded (e.g., Meta Llama 3 8B)

---

### Step 3: Open Your Web App
- Open `template.html` in your browser
- Address: `http://127.0.0.1:15500/template.html` (or wherever you're serving it)

---

## 🧪 Testing

### Test 1: Health Check
```powershell
# In a new PowerShell terminal
curl http://127.0.0.1:5000/health
```

Should return: `{"status":"ok","message":"Server is running"}`

### Test 2: Test Detection Only
Upload a food image to test just ingredient detection (no recipe generation):
```
POST http://127.0.0.1:5000/test-detection
```

---

## 📊 What YOLOv8 Detects

YOLOv8 can detect 80+ common objects including:
- **Food items**: apple, orange, banana, pizza, sandwich, cake, donut, etc.
- **Dishes**: bowl, cup, bottle, plate, fork, knife, spoon
- **Ingredients**: vegetables, fruits, meats (if visible)

> **Note**: YOLOv8 is trained on general objects. For better food detection, you could later switch to a specialized food detection model.

---

## 🔄 How It Works

```
User uploads image
    ↓
Flask Backend receives image
    ↓
YOLOv8 detects ingredients (fast, ~100ms)
    ↓
LM Studio generates recipes from ingredients
    ↓
Frontend displays results with:
    - Detected ingredients + confidence scores
    - Recipe suggestions
    - Instructions
```

---

## ⚙️ Configuration

### Change Detection Sensitivity
In `app.py`, find this line (around line 41):
```python
if confidence > 0.3:  # Change this threshold
```
- Lower value (0.2) = more detections (might have false positives)
- Higher value (0.5) = fewer but more confident detections

### Use More Accurate Model
In `app.py`, line 20:
```python
model = YOLO("yolov8n.pt")  # nano (fastest)
# Options:
# model = YOLO("yolov8s.pt")  # small (balanced)
# model = YOLO("yolov8m.pt")  # medium (more accurate)
# model = YOLO("yolov8l.pt")  # large (slowest)
```

---

## 🆘 Troubleshooting

### "Could not connect to backend"
- Backend not running? Start it with: `.\.venv\Scripts\python.exe app.py`
- Using wrong port? Check it says port 5000

### "Could not connect to LM Studio"
- LM Studio not running? Start it first
- Wrong IP? Check your network IP is `192.168.55.1:1234`

### "No ingredients detected"
- Try a clearer image with actual food/ingredients
- Lower confidence threshold in `app.py` (line 41)

### YOLOv8 model downloading slowly
- First run downloads ~35MB model
- This is normal, wait for it to complete

---

## 📈 Next Steps

1. **Test with sample food images** - take photos of your fridge!
2. **Fine-tune detection sensitivity** if needed
3. **Later: Use specialized food detection models** for better accuracy
4. **Deploy to cloud** (AWS, Heroku, etc.)

---

**Enjoy your Recipe Assistant! 🍳👨‍🍳**
