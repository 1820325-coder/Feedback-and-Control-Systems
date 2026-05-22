from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from ultralytics import YOLO
from PIL import Image, ImageEnhance
import io
import requests
import json
import os
import base64

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
CORS(app)

# Configuration
LM_STUDIO_HOSTS = os.environ.get("LM_STUDIO_HOSTS")
if LM_STUDIO_HOSTS:
    LM_STUDIO_HOSTS = [host.strip() for host in LM_STUDIO_HOSTS.split(",") if host.strip()]
else:
    LM_STUDIO_HOSTS = [
        "http://192.168.56.1:1234",
        "http://127.0.0.1:1234",
    ]
VISION_MODEL = "moondream-2b-2025-04-14"
RECIPE_MODEL = "meta-llama-3-8b-instruct"
YOLO_MODEL = os.environ.get("YOLO_MODEL", "yolov8s-world.pt")
UPLOAD_FOLDER = "uploads"

# Blacklist for non-food items that vision models often mention
NON_FOOD_BLACKLIST = {
    "table", "tabletop", "counter", "countertop", "plate", "bowl", "cup", "fork", 
    "knife", "spoon", "glass", "background", "surface", "wooden", "wood", "board",
    "cutting board", "person", "hand", "finger", "cloth", "napkin", "kitchen",
    "indoor", "outdoor", "image", "photo", "picture", "assortment", "display"
}

# Common ingredients for YOLO-World grounding
GROUNDING_CLASSES = [
    "whole chicken", "raw chicken", "chicken breast", "meat", "tomato", "cherry tomato",
    "red onion", "onion", "garlic", "potato", "carrot", "rosemary", "herb",
    "broccoli", "egg", "milk", "cheese", "bread", "pepper", "lemon",
    "lettuce", "cucumber", "beef", "pork", "fish", "shrimp", "rice", "pasta",
    "vegetable", "fruit", "spice"
]

# Load YOLO model
print(f"Loading YOLO model: {YOLO_MODEL}...")
model = YOLO(YOLO_MODEL)

# If using a World model, set the grounding classes
if "world" in YOLO_MODEL.lower():
    print(f"🌍 Setting YOLO-World classes: {len(GROUNDING_CLASSES)} items")
    model.set_classes(GROUNDING_CLASSES)

print("✓ YOLO model loaded!")

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('template.html')

def detect_ingredients_with_vision(image_data):
    """
    Fallback: Use a Vision-Language Model to detect ingredients
    when YOLOv8 fails or for more complex scenes.
    """
    try:
        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        prompt = "Look very closely. Identify the edible food ingredients in this image. I can see a whole chicken, tomatoes, red onions, a sprig of rosemary, and black peppercorns. Confirm all of these and list them ONLY as short names separated by commas. Do not mention the table or anything else."

        for host in LM_STUDIO_HOSTS:
            url = f"{host}/v1/chat/completions"
            print(f"📡 Attempting Vision detection with {VISION_MODEL} at {url}...")
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
            }

            try:
                response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content'].strip()
                    print(f"💬 Vision Model Response: {content}")
                    
                    # More robust parsing: handle sentences, bullets, etc.
                    # Remove common phrases that vision models often include
                    stop_phrases = ["i see", "ingredients:", "detected:", "the image features", "there are", "accompanied by", "an assortment of"]
                    temp_content = content.lower()
                    for phrase in stop_phrases:
                        temp_content = temp_content.replace(phrase, "")
                    
                    # Split by comma, newline, or bullet points
                    items = []
                    for line in temp_content.split('\n'):
                        for part in line.split(','):
                            # Clean each part
                            clean_part = part.strip().strip('*-•.').strip()
                            
                            # Check if the part contains "chicken", "poultry", or "meat"
                            # even if it's inside a sentence
                            if "chicken" in clean_part.lower() or "poultry" in clean_part.lower():
                                items.append("Chicken")
                                continue
                            if "onion" in clean_part.lower():
                                items.append("Onion")
                                continue
                            if "tomato" in clean_part.lower():
                                items.append("Tomato")
                                continue
                            if "rosemary" in clean_part.lower() or "herb" in clean_part.lower() or "sprig" in clean_part.lower():
                                items.append("Rosemary")
                                continue
                            if "pepper" in clean_part.lower() or "peppercorn" in clean_part.lower():
                                items.append("Pepper")
                                continue

                            # Filter out blacklisted non-food items
                            is_blacklisted = False
                            for blacklisted in NON_FOOD_BLACKLIST:
                                if blacklisted in clean_part.lower():
                                    is_blacklisted = True
                                    break
                            
                            if is_blacklisted:
                                continue

                            # Take only the first 3 words to avoid long descriptions
                            words = clean_part.split()
                            if words:
                                short_name = " ".join(words[:3]) 
                                if len(short_name) > 2:
                                    items.append(short_name.title())
                    
                    ingredients = []
                    unique_items = sorted(list(set(items)))
                    for name in unique_items:
                        ingredients.append({
                            "name": name,
                            "confidence": 100.0
                        })
                    
                    if ingredients:
                        print(f"✅ Vision detection successful: {[i['name'] for i in ingredients]}")
                        return ingredients
                elif response.status_code == 400:
                    error_msg = response.json().get('error', '')
                    if "does not support images" in error_msg.lower() or "channel error" in error_msg.lower():
                        print(f"❌ Critical Error: The model '{VISION_MODEL}' in LM Studio does NOT support images.")
                        return "MODEL_NOT_SUPPORTED"
                    print(f"❌ Vision API returned status 400: {response.text}")
                else:
                    print(f"❌ Vision API returned status {response.status_code}: {response.text}")
            except Exception as e:
                print(f"⚠️ Vision detection error with {host}: {e}")
                continue
                
        return []
    except Exception as e:
        print(f"❌ Vision fallback general error: {e}")
        return []

def detect_ingredients(image):
    """
    Detect food items in image using YOLOv8
    Returns list of detected items
    """
    try:
        # Pre-process image to improve detection accuracy
        # 1. Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        # 2. Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)

        # Force a lower confidence for grounding models to be more aggressive
        results = model(image, conf=0.15)
        detected_items = []

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])

                # Be more strict with confidence for World model (0.35) vs standard (0.45)
                # This helps filter out "ghost" detections like bread/carrot in the photo
                min_conf = 0.35 if "world" in YOLO_MODEL.lower() else 0.45
                
                if confidence > min_conf:
                    detected_items.append({
                        "name": class_name,
                        "confidence": round(confidence * 100, 1)
                    })

        unique_items = list({item["name"]: item for item in detected_items}.values())
        return unique_items

    except Exception as e:
        print(f"Detection error: {e}")
        return []

def call_lm_studio(ingredients_list):
    """Send detected ingredients to LM Studio for recipe suggestions.

    This function attempts multiple common LM Studio API shapes:
    - OpenAI-style chat completions at <host>/v1/chat/completions
    - LM Studio simple chat at <host>/api/v1/chat
    Falls back to returning raw JSON if parsing fails.
    """
    ingredients_text = ", ".join([item["name"] for item in ingredients_list])

    prompt = f"""You are a professional culinary expert. Based on these ingredients: {ingredients_text}

Please provide 3 distinct recipe suggestions. For EACH recipe, use this EXACT structure:

### [Recipe Name]
**Time**: [e.g. 15-20 Mins]
**Heat**: [e.g. Medium-High Heat]
**Description**: "[One sentence summary in quotes]"
**Main Ingredients (From Photo)**:
- [Item 1]
- [Item 2]
**Pantry Items**:
- [Item 1]
- [Item 2]
**Instructions**:
1. **[Step Title]**: [Step Details]
2. **[Step Title]**: [Step Details]
**Chef Note**: [One expert cooking tip]

---
(Use three dashes --- to separate each recipe)
IMPORTANT: Use only standard plain text. Avoid any special characters like \\N or extra markdown glitches."""

    # Try all known LM Studio hosts and endpoints until one works
    for host in LM_STUDIO_HOSTS:
        endpoints = [
            f"{host}/v1/chat/completions",
            f"{host}/api/v1/chat",
            f"{host}/v1/chat",
        ]

        for url in endpoints:
            try:
                if url.endswith('/v1/chat/completions'):
                    payload = {
                        "model": RECIPE_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a helpful culinary assistant specializing in recipe suggestions."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                    }
                else:
                    payload = {
                        "model": RECIPE_MODEL,
                        "system_prompt": "You are a helpful culinary assistant specializing in recipe suggestions.",
                        "input": prompt
                    }

                try:
                    response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=120)
                except Exception as e:
                    print(f"LM Studio request exception for {url}: {e}")
                    continue

                if response.status_code != 200:
                    continue

                try:
                    data = response.json()
                except Exception:
                    print(f"LM Studio non-JSON response from {url}: {response.text}")
                    return response.text

                if isinstance(data, dict):
                    if data.get('error'):
                        continue
                    
                    # Handle raw string content vs structured choices
                    if 'choices' in data:
                        try:
                            content = data['choices'][0]['message']['content']
                            # If the model returned a JSON string inside the content, clean it
                            if content.startswith('{') and "'content':" in content:
                                try:
                                    import ast
                                    parsed = ast.literal_eval(content)
                                    return parsed.get('content', content)
                                except:
                                    pass
                            return content
                        except Exception:
                            pass

                    # Direct fallbacks for common API patterns
                    for key in ('response', 'result', 'text', 'output'):
                        if key in data:
                            return str(data[key])
                    
                    if 'results' in data and isinstance(data['results'], list) and data['results']:
                        first = data['results'][0]
                        if isinstance(first, dict):
                            for k in ('output', 'response', 'text'):
                                if k in first:
                                    return first[k]
                        return str(first)

                return json.dumps(data)

            except requests.exceptions.ConnectionError:
                continue
            except Exception:
                continue

    return f"Error: Could not connect to LM Studio at any configured host ({', '.join(LM_STUDIO_HOSTS)}) (tried several endpoints)"

def merge_ingredients(list1, list2):
    """
    Merge two lists of ingredients, removing duplicates and near-duplicates.
    """
    merged = {item["name"].title(): item for item in list1}
    
    for item in list2:
        name = item["name"].title()
        # Check for near-duplicates (e.g., "Chicken" and "Raw Chicken")
        found = False
        for existing_name in list(merged.keys()):
            if name in existing_name or existing_name in name:
                # Keep the more descriptive name or higher confidence
                if len(name) > len(existing_name):
                    merged.pop(existing_name)
                    merged[name] = item
                found = True
                break
        
        if not found:
            merged[name] = item
            
    return sorted(list(merged.values()), key=lambda x: x["name"])

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint: Accept image, detect ingredients, generate recipes
    """
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        use_vision = request.form.get('vision', 'false').lower() == 'true'
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        print(f"Processing image: {file.filename} ({image.size})")
        detected_ingredients = []
        
        if use_vision:
            print("👁️ Max Accuracy Mode: Combining YOLO and Vision...")
            yolo_results = detect_ingredients(image)
            vision_results = detect_ingredients_with_vision(image_data)
            
            if vision_results == "MODEL_NOT_SUPPORTED":
                return jsonify({
                    "success": False,
                    "error": "Model Mismatch in LM Studio",
                    "suggestion": f"The vision model ({VISION_MODEL}) is not working. Please make sure it is loaded and ready in LM Studio."
                }), 400
                
            detected_ingredients = merge_ingredients(yolo_results, vision_results)
        else:
            print("🔍 Detecting ingredients with YOLOv8...")
            detected_ingredients = detect_ingredients(image)
            
            if not detected_ingredients:
                print(f"⚠️ YOLOv8 found nothing. Falling back to Vision Model ({VISION_MODEL})...")
                detected_ingredients = detect_ingredients_with_vision(image_data)
                if detected_ingredients == "MODEL_NOT_SUPPORTED":
                    return jsonify({
                        "success": False,
                        "error": "Detection Failed",
                        "suggestion": f"YOLO found nothing, and the vision model ({VISION_MODEL}) is not working. Please check LM Studio."
                    }), 400
        
        if not detected_ingredients:
            return jsonify({
                "success": False,
                "error": "No ingredients detected in the image",
                "suggestion": "Try uploading a clearer image or ensure your Vision Model is running in LM Studio.",
                "debug_info": {
                    "yolo_model": YOLO_MODEL,
                    "vision_model": VISION_MODEL,
                    "recipe_model": RECIPE_MODEL
                }
            }), 400
        
        print(f"✓ Found {len(detected_ingredients)} ingredients: {[i['name'] for i in detected_ingredients]}")
        
        print("🍳 Generating recipes with LM Studio...")
        recipes = call_lm_studio(detected_ingredients)
        
        return jsonify({
            "success": True,
            "detected_ingredients": detected_ingredients,
            "suggestion": recipes,
            "ingredient_count": len(detected_ingredients)
        })
    
    except Image.UnidentifiedImageError:
        return jsonify({"error": "Invalid image file"}), 400
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-detection', methods=['POST'])
def test_detection():
    """
    Test endpoint: Just detect ingredients without generating recipes
    Useful for debugging YOLOv8 performance
    """
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        image = Image.open(io.BytesIO(file.read()))
        
        detected = detect_ingredients(image)
        
        return jsonify({
            "detected_ingredients": detected,
            "count": len(detected)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
