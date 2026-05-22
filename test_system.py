"""
Quick test script to verify YOLOv8 + Flask + LM Studio integration
Run this before starting the full web app
"""

import sys
import requests
from pathlib import Path
import os

# Fix encoding for Windows terminal
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_backend_running():
    """Test if Flask backend is running"""
    print("\n1️⃣  Testing Flask Backend...")
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=2)
        if response.status_code == 200:
            print("   ✅ Backend is running on http://127.0.0.1:5000")
            return True
        else:
            print("   ❌ Backend returned error:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend not running!")
        print("   → Start it with: .venv\\Scripts\\python.exe app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_lm_studio_models():
    """Test if LM Studio has a vision-capable model loaded"""
    print("\n2️⃣  Testing LM Studio Models...")
    try:
        # Try local host first
        hosts = ["http://127.0.0.1:1234", "http://192.168.56.1:1234", "http://192.168.55.1:1234"]
        found = False
        for host in hosts:
            try:
                response = requests.get(f"{host}/v1/models", timeout=2)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    print(f"   ✅ Connected to LM Studio at {host}")
                    if models:
                        print(f"   📦 Currently loaded model: {models[0].get('id')}")
                        model_id = models[0].get('id').lower()
                        # Check if it's a known vision model
                        vision_keywords = ['llava', 'moondream', 'vision', 'vlm', 'minicpm']
                        is_vision = any(k in model_id for k in vision_keywords)
                        if is_vision:
                            print("      ✅ This model appears to support Vision!")
                        else:
                            print("      ⚠️  Warning: This model might NOT support images.")
                            print("      → Please load a model like 'LLaVA' or 'Moondream' for image analysis.")
                    else:
                        print("      ❌ No models are currently loaded in LM Studio.")
                    found = True
                    break
            except:
                continue
        
        if not found:
            print("   ❌ Could not connect to LM Studio on any common port.")
            return False
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_yolo_availability():
    """Test if YOLOv8 model is loaded"""
    print("\n3️⃣  Testing YOLOv8...")
    try:
        from ultralytics import YOLO
        print("   ✅ YOLOv8 package is installed")
        print("   ℹ️  Model will be loaded when you start the backend")
        print("      (First run downloads ~35MB - takes 1-2 minutes)")
        return True
    except ImportError:
        print("   ❌ YOLOv8 not installed!")
        print("   → Run: pip install ultralytics")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("\n" + "="*50)
    print("🧪 Recipe Assistant - System Check")
    print("="*50)
    
    results = {
        "Backend": test_backend_running(),
        "LM Studio": test_lm_studio_models(),
        "YOLO-World": test_yolo_availability(),
    }
    
    print("\n" + "="*50)
    print("📊 Status Summary:")
    print("="*50)
    
    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}: {'Ready' if status else 'Not Ready'}")
    
    all_ready = all(results.values())
    
    if all_ready:
        print("\n" + "="*50)
        print("🎉 All systems ready!")
        print("You can now open template.html in your browser")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("⚠️  Some systems are not ready!")
        print("Please check the errors above")
        print("="*50)
    
    return 0 if all_ready else 1

if __name__ == "__main__":
    sys.exit(main())
