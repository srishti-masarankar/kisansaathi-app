import io, torch, timm
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from torchvision import transforms as T
from pydantic import BaseModel
from advice import get_advice, get_weather, get_risk, get_spray_windows
from llm import ask_llm, ask_rag
from gradcam import gradcam_overlay
from mandi import get_mandi_price
from radar import add_report, summary, seed_demo, clear_demo, TALUKAS
THRESHOLD = 0.40

ckpt = torch.load('combined_model.pth', map_location='cpu')
classes = ckpt['classes']
model = timm.create_model('efficientnet_b0', num_classes=len(classes))
model.load_state_dict(ckpt['model']); model.eval()

tf = T.Compose([T.Resize((224,224)), T.ToTensor(),
                T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
app = FastAPI()

def pretty(name):
    return name.replace('___', ' - ').replace('_', ' ').strip()

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read())).convert('RGB')
    x = tf(img).unsqueeze(0)
    with torch.no_grad():
        p = torch.softmax(model(x), 1)[0]
    top = p.topk(3)
    results = [{"disease": pretty(classes[i]), "confidence": round(v.item(), 3)}
               for v, i in zip(top.values, top.indices)]
    out = {"sure": results[0]["confidence"] >= THRESHOLD, "results": results}
    try:
        out["heatmap"] = gradcam_overlay(model, x, img, int(top.indices[0]))
    except Exception as e:
        print("gradcam failed:", e)
    if out["sure"]:
        out["class"] = classes[top.indices[0]]
        out["advice"] = get_advice(classes[top.indices[0]])
        out["weather"] = get_weather()
        out["risk"] = get_risk(classes[top.indices[0]])
    return out

class Ask(BaseModel):
    question: str
    disease: str | None = None

@app.post("/ask")
def ask(a: Ask):
    return ask_rag(a.question, a.disease)

@app.get("/spray-windows")
def spray_windows():
    return get_spray_windows()

@app.get("/mandi")
def mandi(commodity: str):
    return get_mandi_price(commodity)

class Report(BaseModel):
    disease: str
    taluka: str

@app.post("/radar/report")
def radar_report(r: Report):
    if r.disease not in classes or "healthy" in r.disease.lower() or r.taluka not in TALUKAS:
        return {"ok": False}
    add_report(r.disease, r.taluka)
    return {"ok": True}

@app.get("/radar/summary")
def radar_summary():
    return summary()

@app.post("/radar/demo")
def radar_demo():
    seed_demo(); return {"ok": True}

@app.delete("/radar/demo")
def radar_demo_clear():
    clear_demo(); return {"ok": True}

@app.get("/")
def home():
    return FileResponse("index.html")
