import json, urllib.request
from datetime import datetime, timedelta

LAT, LON = 16.705, 74.243   # Kolhapur
CONFIRM_EN = "Confirm any spray choice with your local agriculture officer"
CONFIRM_MR = "कोणतीही फवारणी करण्यापूर्वी स्थानिक कृषी अधिकाऱ्यांचा सल्ला घ्या"

# Your original hand-written entries (English) - kept as they are
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

# Disease TYPES (matched by keyword, so every class gets advice, English + Marathi).
# temp = favourable temperature range (C); wet = what weather helps it spread
TYPES = {
 "late_blight": dict(temp=(10,24), wet="wet",
   en=("Fast-spreading disease with water-soaked patches, worse in cool wet weather.",
       ["Remove infected plants quickly","Spray a recommended fungicide before rain","Avoid overhead watering","Keep plants spaced for airflow"]),
   mr=("पाण्यासारखे डाग पडणारा झपाट्याने पसरणारा रोग; थंड व दमट हवेत जास्त वाढतो.",
       ["बाधित झाडे लगेच काढून नष्ट करा","पावसापूर्वी शिफारस केलेली बुरशीनाशक फवारणी करा","वरून पाणी देणे टाळा","हवा खेळती राहण्यासाठी झाडांमध्ये अंतर ठेवा"])),
 "leaf_spot": dict(temp=(20,30), wet="wet",
   en=("Fungal leaf disease with spots or rings on the leaves.",
       ["Remove and destroy infected leaves","Spray a recommended fungicide","Water at the base, not on the leaves","Rotate crops next season"]),
   mr=("पानांवर डाग किंवा वलये पडणारा बुरशीजन्य रोग.",
       ["बाधित पाने काढून नष्ट करा","शिफारस केलेली बुरशीनाशक फवारणी करा","पानांवर नाही, झाडाच्या बुडाशी पाणी द्या","पुढच्या हंगामात पीक फेरपालट करा"])),
 "rust": dict(temp=(15,28), wet="wet",
   en=("Fungal disease with orange, brown or rusty pustules on leaves.",
       ["Remove heavily infected leaves","Spray a recommended fungicide early","Avoid overhead watering","Remove nearby alternate host plants if known"]),
   mr=("पानांवर नारिंगी किंवा तांबूस फोडे येणारा बुरशीजन्य रोग (तांबेरा).",
       ["जास्त बाधित पाने काढा","सुरुवातीलाच शिफारस केलेली बुरशीनाशक फवारणी करा","वरून पाणी देणे टाळा","शक्य असल्यास जवळची पर्यायी यजमान झाडे काढा"])),
 "scab": dict(temp=(10,24), wet="wet",
   en=("Fungal disease with dark scabby spots on leaves and fruit.",
       ["Rake and destroy fallen leaves","Spray a recommended fungicide","Prune for airflow"]),
   mr=("पाने व फळांवर काळे खपल्यासारखे डाग पडणारा बुरशीजन्य रोग.",
       ["गळलेली पाने गोळा करून नष्ट करा","शिफारस केलेली बुरशीनाशक फवारणी करा","हवा खेळती राहण्यासाठी छाटणी करा"])),
 "mildew": dict(temp=(18,30), wet="humid",
   en=("Fungal disease with white powdery coating on leaves.",
       ["Remove badly affected leaves","Spray a recommended fungicide or wettable sulphur","Improve spacing and airflow","Avoid too much nitrogen fertiliser"]),
   mr=("पानांवर पांढरी भुकटीसारखी पूड दिसणारा बुरशीजन्य रोग (भुरी).",
       ["जास्त बाधित पाने काढा","शिफारस केलेले बुरशीनाशक किंवा ओले होणारे गंधक फवारा","झाडांमध्ये अंतर ठेवून हवा खेळती ठेवा","नत्र खताचा अतिरेक टाळा"])),
 "mold": dict(temp=(18,28), wet="wet",
   en=("Fungal disease with yellow patches on top and mould underneath the leaf, common in humid conditions.",
       ["Improve airflow and ventilation","Remove infected leaves","Spray a recommended fungicide","Avoid wetting leaves"]),
   mr=("पानाच्या वर पिवळे डाग व खाली बुरशी दिसणारा रोग; दमट हवेत जास्त.",
       ["हवा खेळती ठेवा","बाधित पाने काढा","शिफारस केलेली बुरशीनाशक फवारणी करा","पाने ओली होऊ देऊ नका"])),
 "bacterial": dict(temp=(22,32), wet="wet",
   en=("Bacterial disease with small dark spots, spread by water splash.",
       ["Remove infected leaves","Use a copper-based spray as advised locally","Avoid working in wet fields","Use clean seed"]),
   mr=("पाण्याच्या उडण्यातून पसरणारा, लहान काळे डाग पाडणारा जिवाणूजन्य रोग.",
       ["बाधित पाने काढा","स्थानिक सल्ल्यानुसार तांबेयुक्त फवारणी करा","ओल्या शेतात काम करणे टाळा","निरोगी बियाणे वापरा"])),
 "virus": dict(temp=(24,35), wet="dry",
   en=("Viral disease spread by insects like whitefly and aphids. No spray cures the virus itself.",
       ["Remove and destroy infected plants","Control whitefly/aphids (yellow sticky traps, neem oil)","Use virus-free seedlings","Keep weeds away"]),
   mr=("पांढरी माशी व मावा यांसारख्या किडींमार्फत पसरणारा विषाणूजन्य रोग. फवारणीने विषाणू बरा होत नाही.",
       ["बाधित झाडे उपटून नष्ट करा","पांढरी माशी/माव्यावर नियंत्रण ठेवा (पिवळे चिकट सापळे, निंबोळी तेल)","विषाणूमुक्त रोपे वापरा","तण काढून टाका"])),
 "mite": dict(temp=(28,40), wet="dry",
   en=("Tiny sap-sucking mites causing speckled, yellowing leaves, worse in hot dry weather.",
       ["Spray water on the underside of leaves","Use neem oil or a recommended miticide","Remove badly infested leaves","Avoid dusty, water-stressed plants"]),
   mr=("रस शोषणारे सूक्ष्म कोळी; पानांवर ठिपके व पिवळेपणा, उष्ण कोरड्या हवेत जास्त.",
       ["पानांच्या खालच्या बाजूस पाण्याचा फवारा मारा","निंबोळी तेल किंवा शिफारस केलेले कोळीनाशक वापरा","जास्त बाधित पाने काढा","झाडांना पाण्याचा ताण पडू देऊ नका"])),
 "rot": dict(temp=(15,28), wet="wet",
   en=("Fungal disease causing leaf spots and rotting of fruit.",
       ["Remove infected leaves and fruit","Spray a recommended fungicide","Prune for airflow","Clear fallen debris"]),
   mr=("पानांवर डाग व फळे सडवणारा बुरशीजन्य रोग.",
       ["बाधित पाने व फळे काढा","शिफारस केलेली बुरशीनाशक फवारणी करा","हवा खेळती राहण्यासाठी छाटणी करा","गळलेला कचरा साफ करा"])),
 "general": dict(temp=(15,30), wet="wet",
   en=("No stored advice for this disease yet.", ["Consult your local agriculture officer"]),
   mr=("या रोगासाठी अजून सल्ला उपलब्ध नाही.", ["स्थानिक कृषी अधिकाऱ्यांचा सल्ला घ्या"])),
}

# (keyword in class name, type) - first match wins
KEYS = [("late_blight","late_blight"),("virus","virus"),("mosaic","virus"),("curl","virus"),
        ("greening","virus"),("haunglongbing","virus"),("mite","mite"),("powdery","mildew"),
        ("mildew","mildew"),("mold","mold"),("rust","rust"),("scab","scab"),("bacterial","bacterial"),
        ("black_rot","rot"),("esca","rot"),("measles","rot"),("rot","rot"),
        ("blight","leaf_spot"),("spot","leaf_spot"),("scorch","leaf_spot"),("cercospora","leaf_spot")]

def _type(name):
    n = name.lower()
    for k, t in KEYS:
        if k in n:
            return t
    return "general"

def get_advice(name):
    if "healthy" in name.lower():
        return {"about": "The leaf looks healthy.", "steps": ["Keep monitoring regularly", "Maintain good watering and spacing"],
                "about_mr": "पान निरोगी दिसते.", "steps_mr": ["नियमित निरीक्षण करा", "योग्य पाणी व अंतर राखा"]}
    t = TYPES[_type(name)]
    if name in ADVICE:
        about, steps = ADVICE[name]
    else:
        about, steps = t["en"]
    about_mr, steps_mr = t["mr"]
    return {"about": about, "steps": steps + [CONFIRM_EN],
            "about_mr": about_mr, "steps_mr": steps_mr + [CONFIRM_MR]}

def get_weather():
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
               "&daily=precipitation_probability_max&forecast_days=3&timezone=auto")
        with urllib.request.urlopen(url, timeout=5) as r:
            d = json.load(r)["daily"]
        rainy = [t for t, p in zip(d["time"], d["precipitation_probability_max"]) if p is not None and p >= 60]
        if rainy:
            return f"Rain likely on {rainy[0]}. Delay spraying until it clears."
        return "No heavy rain expected in the next 3 days. Good time to spray."
    except Exception:
        return "Weather unavailable (check internet)."

# ---------------- Step 2: disease spread risk forecast ----------------
def _score_days(hourly, rule):
    """hourly: dict with time, temperature_2m, relative_humidity_2m, precipitation. Returns per-day risk."""
    days = {}
    for t, T_, rh, pr in zip(hourly["time"], hourly["temperature_2m"],
                             hourly["relative_humidity_2m"], hourly["precipitation"]):
        if T_ is None or rh is None:
            continue
        d = days.setdefault(t[:10], {"t": [], "rh": [], "rain": 0.0, "wet_h": 0})
        d["t"].append(T_); d["rh"].append(rh); d["rain"] += pr or 0
        d["wet_h"] += rh >= 85
    out = []
    lo, hi = rule["temp"]
    for date, d in sorted(days.items()):
        if len(d["t"]) < 12:
            continue
        mt, mrh = sum(d["t"]) / len(d["t"]), sum(d["rh"]) / len(d["rh"])
        score = 1 if lo <= mt <= hi else 0
        w = rule["wet"]
        if w == "wet":
            score += 2 if d["wet_h"] >= 10 else 1 if (d["wet_h"] >= 5 or d["rain"] >= 2) else 0
        elif w == "humid":
            score += 2 if (mrh >= 60 and d["rain"] < 2) else 1 if mrh >= 50 else 0
        else:  # dry/hot favoured
            score += 2 if mrh < 55 else 1 if mrh < 65 else 0
        out.append({"date": date, "level": "High" if score >= 3 else "Medium" if score == 2 else "Low",
                    "temp": round(mt, 1), "rh": round(mrh), "rain": round(d["rain"], 1)})
    return out

def _summary(days):
    def names(lv, lang):
        loc = "mr" if lang == "mr" else "en"
        return ", ".join(datetime.fromisoformat(x["date"]).strftime("%a %d") for x in days if x["level"] == lv)
    hi = names("High", "en")
    if hi:
        return (f"High spread risk on {hi}. Inspect plants daily and spray protectively before wet spells.",
                f"{hi} रोजी रोग पसरण्याचा धोका जास्त. रोज झाडांची पाहणी करा व ओल्या हवामानापूर्वी संरक्षक फवारणी करा.")
    md = names("Medium", "en")
    if md:
        return (f"Moderate risk on {md}. Keep watching the plants.",
                f"{md} रोजी मध्यम धोका. झाडांवर लक्ष ठेवा.")
    return ("Low spread risk for the next 5 days.", "पुढील ५ दिवस रोग पसरण्याचा धोका कमी.")

def get_risk(name):
    try:
        rule = TYPES[_type(name)] if "healthy" not in name.lower() else TYPES["general"]
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
               "&hourly=temperature_2m,relative_humidity_2m,precipitation&forecast_days=5&timezone=auto")
        with urllib.request.urlopen(url, timeout=6) as r:
            hourly = json.load(r)["hourly"]
        days = _score_days(hourly, rule)
        if not days:
            return None
        en, mr = _summary(days)
        return {"days": days, "summary_en": en, "summary_mr": mr}
    except Exception:
        return None


# ---------------- Step 3: best spray windows ----------------
SPRAY_HOURS = (6, 7, 8, 9, 16, 17, 18)   # cooler morning / evening hours

def _spray_windows(h, now_local):
    n = len(h["time"])
    good = []
    for i, t in enumerate(h["time"]):
        dt = datetime.fromisoformat(t)
        if dt < now_local.replace(minute=0, second=0, microsecond=0) or dt.hour not in SPRAY_HOURS:
            continue
        ahead = range(i, min(i + 4, n))               # must stay dry for the next 4 hours
        rain = sum(h["precipitation"][j] or 0 for j in ahead)
        prob = max((h["precipitation_probability"][j] or 0) for j in ahead)
        w, T_ = h["wind_speed_10m"][i], h["temperature_2m"][i]
        if rain == 0 and prob <= 30 and w is not None and T_ is not None and 2 <= w <= 15 and T_ <= 32:
            good.append((dt, w, T_, prob))
    wins, cur = [], []
    for g in good:
        if cur and g[0] - cur[-1][0] != timedelta(hours=1):
            wins.append(cur); cur = []
        cur.append(g)
    if cur:
        wins.append(cur)
    return [{"date": c[0][0].date().isoformat(), "start": c[0][0].hour, "end": c[-1][0].hour + 1,
             "wind": round(sum(x[1] for x in c) / len(c)), "temp": round(sum(x[2] for x in c) / len(c)),
             "prob": max(x[3] for x in c)} for c in wins][:4]

def get_spray_windows():
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
               "&hourly=temperature_2m,precipitation_probability,precipitation,wind_speed_10m"
               "&forecast_days=3&timezone=auto")
        with urllib.request.urlopen(url, timeout=6) as r:
            d = json.load(r)
        now_local = datetime.utcnow() + timedelta(seconds=d.get("utc_offset_seconds", 19800))
        return {"windows": _spray_windows(d["hourly"], now_local)}
    except Exception:
        return {"windows": [], "error": True}
