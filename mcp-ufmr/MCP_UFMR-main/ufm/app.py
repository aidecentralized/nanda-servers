import streamlit as st
from PIL import Image
import torch
import torchvision.transforms as T
import base64
import io

from agent import FederatedUFMSystem
from utils import plot_patch_overlay_on_image

st.set_page_config(page_title="Federated UFM Diagnosis", layout="wide")
st.title("🩺 Federated UFM Diagnosis System")

st.markdown("Upload an X-ray, enter patient data, and let multiple agents collaborate for a diagnosis.")

# Sidebar: Patient Info
st.sidebar.header("Patient Info")
patient_id = st.sidebar.text_input("Patient ID", value="patient_001")
age = st.sidebar.number_input("Age", min_value=0, max_value=120, value=45)
bp = st.sidebar.number_input("Blood Pressure", min_value=50, max_value=200, value=120)
hr = st.sidebar.number_input("Heart Rate", min_value=30, max_value=200, value=80)

# Text Report
report = st.text_area("Clinical Report", height=150, placeholder="Describe symptoms, findings, etc.")

# File uploader
xray_file = st.file_uploader("Upload X-ray Image (PNG or JPG)", type=["png", "jpg", "jpeg"])

# Process Button
if st.button("🔍 Run Diagnosis"):
    if not xray_file or not report.strip() or not patient_id:
        st.warning("Please fill out all fields and upload an X-ray.")
    else:
        try:
            img = Image.open(xray_file).convert("RGB")
            st.image(img, caption="Uploaded X-ray", width=300)

            # Preprocess image and tabular input
            transform = T.Compose([T.Resize((224, 224)), T.ToTensor()])
            img_tensor = transform(img).unsqueeze(0)
            tab_tensor = torch.tensor([[age, bp, hr]], dtype=torch.float32)

            # Run through Federated system
            fed = FederatedUFMSystem(num_agents=3)
            results = fed.run_all(tab_tensor, report, img_tensor, patient_id)

            decisions, confidences = zip(*[(r[1], r[2]) for r in results])
            majority_label = max(set(decisions), key=decisions.count)
            majority_diagnosis = "Pneumonia" if majority_label.lower() != "normal" else "Normal"

            st.success(f"🧠 Majority Diagnosis: **{majority_diagnosis}**")

            st.subheader("📊 Agent Predictions")
            for r in results:
                st.write(f"- **Agent {r[0]}**: {r[1]} (Confidence: {round(r[2], 4)})")

            agent_1 = fed.agents[0]
            memory = agent_1.memory[patient_id]

            # Overlay Visualization
            overlay_path = plot_patch_overlay_on_image(memory["img_contribs"], 10, 10, img_tensor)
            with open(overlay_path, "rb") as f:
                encoded_overlay = base64.b64encode(f.read()).decode("utf-8")
            st.image(overlay_path, caption="🔍 Patch Attention Overlay (Agent 1)", use_column_width=True)

            # Token & Attention
            tokenizer = agent_1.tokenizer
            token_ids = tokenizer(report, return_tensors="pt", padding="max_length", truncation=True, max_length=64)["input_ids"][0]
            tokens = tokenizer.convert_ids_to_tokens(token_ids)
            scores = memory["attn"][0].detach().cpu().numpy().flatten()
            top_tokens = sorted([
                (tokens[i], float(scores[i])) for i in range(min(len(tokens), len(scores))) if tokens[i] != "<pad>"
            ], key=lambda x: x[1], reverse=True)[:10]

            st.subheader("🧠 Agent 1 Text Attention")
            for token, score in top_tokens:
                st.write(f"**{token}**: {round(score, 4)}")

            tab_contribs = [
                float(val.flatten()[0].item() if val.numel() > 1 else val.item())
                for val in memory["tab_contribs"]
            ]

            st.subheader("📈 Agent 1 Tabular Contributions")
            st.json({
                "Age": round(tab_contribs[0], 4),
                "BP": round(tab_contribs[1], 4),
                "HR": round(tab_contribs[2], 4)
            })

        except Exception as e:
            st.error(f"❌ Error during diagnosis: {str(e)}")
