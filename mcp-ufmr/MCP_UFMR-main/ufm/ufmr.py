import os
import sys
import socket
import logging
import traceback
from flask import Flask, request, jsonify
from PIL import Image, ImageFont, ImageDraw
import torch
import torchvision.transforms as T
import base64
import numpy as np
import cv2
from torchvision.transforms.functional import to_pil_image

# Optional: block stdout for Claude (enable only in production)
# sys.stdout = open(os.devnull, 'w')

# Initialize Flask app
app = Flask(__name__)

# Import internal components (make sure they're silent!)
from agent import FederatedUFMSystem

# ---------- Patch Overlay Utility ----------
def plot_patch_overlay_on_image(patch_tensor, h, w, image_tensor):
    patch_tensor = patch_tensor.squeeze()
    if isinstance(patch_tensor, torch.Tensor):
        patch_tensor = patch_tensor.detach().cpu().numpy()

    patch_tensor = (patch_tensor - patch_tensor.min()) / (patch_tensor.max() - patch_tensor.min() + 1e-8)
    heatmap = patch_tensor.reshape(h, w)

    heatmap_resized = cv2.resize((heatmap * 255).astype(np.uint8), (224, 224), interpolation=cv2.INTER_CUBIC)
    colored_heatmap = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_MAGMA)

    if len(image_tensor.shape) == 4:
        image_tensor = image_tensor.squeeze(0)
    image_pil = to_pil_image(image_tensor)
    image_np = np.array(image_pil)
    if image_np.dtype != np.uint8:
        image_np = (image_np * 255).astype(np.uint8)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    blended = cv2.addWeighted(image_bgr, 0.6, colored_heatmap, 0.4, 0)
    blended_rgb = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
    final_image = Image.fromarray(blended_rgb)

    # Create vertical colorbar with value labels
    bar_height, bar_width = 224, 50
    gradient = np.linspace(1.0, 0.0, bar_height)[:, None]
    gradient_img = np.uint8(gradient * 255)
    gradient_img = np.repeat(gradient_img, bar_width, axis=1)
    colorbar = cv2.applyColorMap(gradient_img, cv2.COLORMAP_MAGMA)
    colorbar_rgb = cv2.cvtColor(colorbar, cv2.COLOR_BGR2RGB)
    colorbar_pil = Image.fromarray(colorbar_rgb)

    draw = ImageDraw.Draw(colorbar_pil)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()

    for i in range(6 + 1):
        value = 1.0 - i / 6
        y = int(i * (bar_height / 6)) - 6
        label = f"{value:.1f}"
        try:
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            text_width, _ = font.getsize(label)
        draw.text(((bar_width - text_width) / 2, y), label, fill="white", font=font)

    spacing = 10
    total_width = final_image.width + spacing + colorbar_pil.width
    combined = Image.new("RGB", (total_width, 224), color=(0, 0, 0))
    combined.paste(final_image, (0, 0))
    combined.paste(colorbar_pil, (final_image.width + spacing, 0))

    path = f"overlay_{int(torch.randint(10000, (1,)).item())}.png"
    combined.save(path)
    return path

# ---------- Claude MCP Initialize ----------
@app.route("/", methods=["POST"])
def initialize():
    try:
        print(f"📡 /initialize Content-Type: {request.content_type}", file=sys.stderr)

        if request.content_type != "application/json":
            print("❌ Invalid content type", file=sys.stderr)
            return jsonify({"error": "Invalid content type"}), 400

        data = request.get_json(force=True)
        print(f"📥 Init Payload: {data}", file=sys.stderr)

        if data and data.get("method") == "initialize":
            print("✅ Valid MCP initialize", file=sys.stderr)
            return jsonify({
                "jsonrpc": "2.0",
                "id": data["id"],
                "result": {
                    "serverInfo": {
                        "name": "ufm-server",
                        "version": "0.1.0"
                    },
                    "capabilities": {}
                }
            })
        else:
            print("❌ Missing or invalid method", file=sys.stderr)
            return jsonify({"error": "Invalid method"}), 400

    except Exception as e:
        print(f"❌ MCP Init Exception: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 500

# ---------- Diagnosis Endpoint ----------
@app.route("/functions/diagnose", methods=["POST"])
def diagnose():
    print("✅ /functions/diagnose endpoint hit", file=sys.stderr)
    try:
        patient_id = request.form['patient_id'].strip()
        age = int(request.form['age'])
        bp = int(request.form['bp'])
        hr = int(request.form['hr'])
        report = request.form['report']
        xray_file = request.files['xray_image']

        print(f"📥 Received: ID={patient_id}, Age={age}, BP={bp}, HR={hr}", file=sys.stderr)

        try:
            img = Image.open(xray_file.stream).convert("RGB")
        except Exception as e:
            print(f"❌ Invalid image: {e}", file=sys.stderr)
            return jsonify({"error": "Uploaded file is not a valid image"}), 400

        transform = T.Compose([T.Resize((224, 224)), T.ToTensor()])
        img_tensor = transform(img).unsqueeze(0)
        tab_tensor = torch.tensor([[age, bp, hr]], dtype=torch.float32)

        fed = FederatedUFMSystem(num_agents=3)
        results = fed.run_all(tab_tensor, report, img_tensor, patient_id)

        decisions, confidences = zip(*[(r[1], r[2]) for r in results])
        majority_label = max(set(decisions), key=decisions.count)
        majority_diagnosis = "Pneumonia" if majority_label.lower() != "normal" else "Normal"

        agent_1 = fed.agents[0]
        memory = agent_1.memory.get(patient_id)
        if memory is None:
            raise RuntimeError(f"No memory found for patient ID: {patient_id}")

        overlay_path = plot_patch_overlay_on_image(memory["img_contribs"], 10, 10, img_tensor)
        with open(overlay_path, "rb") as f:
            encoded_overlay = base64.b64encode(f.read()).decode("utf-8")

        tokenizer = agent_1.tokenizer
        token_ids = tokenizer(report, return_tensors="pt", padding="max_length", truncation=True, max_length=64)["input_ids"][0]
        tokens = tokenizer.convert_ids_to_tokens(token_ids)
        scores = memory["attn"][0].detach().cpu().numpy().flatten()
        top_tokens = sorted([
            (tokens[i], float(scores[i])) for i in range(min(len(tokens), len(scores))) if tokens[i] != "<pad>"
        ], key=lambda x: x[1], reverse=True)[:10]

        tab_contribs = [
            float(val.flatten()[0].item() if val.numel() > 1 else val.item())
            for val in memory["tab_contribs"]
        ]

        print("✅ Diagnosis complete", file=sys.stderr)
        return jsonify({
            "majority_diagnosis": majority_diagnosis,
            "agent_predictions": [
                {"agent": r[0], "label": r[1], "probability": round(r[2], 4)} for r in results
            ],
            "agent_1_diagnosis": {
                "label": "Pneumonia" if confidences[0] > 0.5 else "Normal",
                "confidence": round(confidences[0], 4),
                "top_text_tokens": top_tokens,
                "tabular_contributions": {
                    "Age": round(tab_contribs[0], 4),
                    "BP": round(tab_contribs[1], 4),
                    "HR": round(tab_contribs[2], 4)
                },
                "patch_overlay_base64": encoded_overlay
            }
        })

    except Exception as e:
        print(f"❌ Diagnosis error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 500

# ---------- Start Server ----------
if __name__ == "__main__":
    try:
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        port = int(os.environ.get("PORT", 5059))
        print(f"🚀 Federated UFM Flask server running on port {port}", file=sys.stderr)
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Server failed to start: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
