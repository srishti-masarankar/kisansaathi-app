import json, urllib.request

ADVICE = {
 "Tomato___Early_blight": ("Fungal disease with dark ringed spots on older leaves.",
   ["Remove and destroy infected leaves", "Spray a recommended fungicide (for example copper-based or mancozeb)",
    "Water at the base, not on the leaves", "Rotate crops next season"]),
 "Tomato___Late_blight": ("Fast-spreading disease with water-soaked patches, worse in cool wet weather.",
   ["Remove infected plants quickly", "Spray a recommended fungicide before rain", "Avoid overhead watering", "Keep plants spaced for airflow"]),
 "Tomato___Septoria_leaf_spot": ("Fungal disease with small round spots with dark edges.",
   ["Remove spotted lower leaves", "Spray a recommended fungicide", "Mulch to stop soil splash", "Rotate crops"]),
 "Tomato___Bacterial_spot": ("Bacterial disease with small dark spots, spread by water splash.",
   ["Remove infected leaves", "Use a copper-based spray as advised locally", "Avoid working in wet fields", "Use clean seed"]),
 "Potato___Early_blight": ("Fungal disease with brown ringed spots.",
   ["Remove infected leaves", "Spray a recommended fungicide", "Keep plants well fed and watered", "Rotate crops"]),
 "Potato___Late_blight": ("Serious disease that can destroy a crop within days in wet weather.",
   ["Remove infected plants", "Spray a recommended fungicide before rain", "Avoid overhead watering", "Do not store infected tubers"]),
 "Grape___Black_rot": ("Fungal disease with brown leaf spots and shrivelled black fruit.",
   ["Remove infected leaves and fruit", "Spray a recommended fungicide", "Prune for airflow", "Clear fallen debris"]),
 "Corn_(maize)___Common_rust_": ("Fungal disease with reddish-brown pustules on leaves.",
   ["Plant resistant hybrids", "Spray a fungicide if infection is early and heavy", "Monitor neighbouring fields"]),
 "Corn_(maize)___Northern_Leaf_Blight": ("Fungal disease with long grey-green lesions.",
   ["Use resistant hybrids", "Rotate crops", "Plough under crop residue", "Spray a fungicide if severe"]),
 "Apple___Apple_scab": ("Fungal disease with dark scabby spots on leaves and fruit.",
   ["Rake and destroy fallen leaves", "Spray a recommended fungicide", "Prune for airflow"]),
}

def get_advice(name):
    if "healthy" in name:
        return {"about": "The leaf looks healthy.", "steps": ["Keep monitoring regularly", "Maintain good watering and spacing"]}
    about, steps = ADVICE.get(name, ("No stored advice for this disease yet.", ["Consult your local agriculture officer"]))
    return {"about": about, "steps": steps + ["Confirm any spray choice with your local agriculture officer"]}

def get_weather():
    try:
        url = ("https://api.open-meteo.com/v1/forecast?latitude=16.705&longitude=74.243"
               "&daily=precipitation_probability_max&forecast_days=3&timezone=auto")
        with urllib.request.urlopen(url, timeout=5) as r:
            d = json.load(r)["daily"]
        rainy = [t for t, p in zip(d["time"], d["precipitation_probability_max"]) if p is not None and p >= 60]
        if rainy:
            return f"Rain likely on {rainy[0]}. Delay spraying until it clears."
        return "No heavy rain expected in the next 3 days. Good time to spray."
    except Exception:
        return "Weather unavailable (check internet)."