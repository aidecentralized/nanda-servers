# Nutrition MCP Server 🥗

This is a [Model Context Protocol (MCP)](https://modelcontextprotocol.org) compatible server that provides **nutrition facts** for any food using the **Open Food Facts** API.

It enables AI models or agents to call a simple tool and get back calories, macros, and other useful dietary information.

---

## 🛠️ Tool: `get_nutrition` 🥝

```python
get_nutrition(food: str) → dict
```

Returns a dictionary of nutrition facts for the specified food item. The data is sourced from Open Food Facts and may include:

- Energy (kcal)
- Protein
- Carbohydrates
- Fat
- Fiber
- Sugars
- Sodium
- Serving size
- Nutri-Score (if available)

---

## 🚀 Quickstart

1. **Install dependencies**

   ```bash
   pip install openfoodfacts
   ```

2. **Run the server**

   ```bash
   python mcp_nutri.py
   ```

3. **Use the tool**

   From an MCP-compatible client (like Claude Desktop or Cursor), call:

   ```python
   get_nutrition("banana")
   ```

---

## 📦 Dependencies

- [openfoodfacts](https://pypi.org/project/openfoodfacts/): Official Python SDK for Open Food Facts
- [mcp](https://pypi.org/project/mcp/): Python SDK for Model Context Protocol

---

## 🧪 Example Output

```json
{
  "product_name": "Banana",
  "energy_kcal": 89,
  "protein_g": 1.1,
  "carbohydrates_g": 22.8,
  "fat_g": 0.3,
  "fiber_g": 2.6,
  "sugars_g": 12.2,
  "sodium_mg": 1,
  "serving_size": "100g",
  "nutriscore_grade": "A"
}
```

---

## 📄 License

This project is licensed under the MIT License.

Data is provided by [Open Food Facts](https://world.openfoodfacts.org/) under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).
