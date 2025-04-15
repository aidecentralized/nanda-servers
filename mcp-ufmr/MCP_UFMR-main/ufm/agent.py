
import torch

class DummyAgent:
    def __init__(self, name):
        self.name = name
        self.memory = {}
        self.tokenizer = self.DummyTokenizer()

    def predict(self, tab_tensor, report, img_tensor, patient_id):
        prob = torch.sigmoid(torch.tensor(1.5 - img_tensor.mean())).item()
        decision = "Pneumonia" if prob > 0.5 else "Normal"
        self.memory[patient_id] = {
            "prediction": decision,
            "probability": prob,
            "img_contribs": torch.rand((10, 10)),
            "attn": torch.rand((1, 64)),
            "tab_contribs": [torch.rand(1), torch.rand(1), torch.rand(1)],
            "notes": "Auto-diagnosed"
        }
        return decision, prob

    def last(self, patient_id):
        return self.memory.get(patient_id, {})

    class DummyTokenizer:
        def convert_ids_to_tokens(self, input_ids):
            return [f"token_{i}" for i in range(len(input_ids))]

        def __call__(self, text, **kwargs):
            return {"input_ids": torch.arange(64).unsqueeze(0)}

class FederatedUFMSystem:
    def __init__(self, num_agents=3):
        self.agents = [DummyAgent(f"Agent-{i+1}") for i in range(num_agents)]

    def run_all(self, tab_tensor, report, img_tensor, patient_id):
        results = []
        for agent in self.agents:
            decision, prob = agent.predict(tab_tensor, report, img_tensor, patient_id)
            results.append((agent.name, decision, prob))
        return results
