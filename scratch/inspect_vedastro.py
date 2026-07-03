import json

with open("scratch/vedastro_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Keys in vedastro_output.json:", data.keys() if isinstance(data, dict) else type(data))
if isinstance(data, dict):
    for k, v in data.items():
        print(k, type(v))
        if isinstance(v, dict):
            print("  Subkeys:", v.keys())
