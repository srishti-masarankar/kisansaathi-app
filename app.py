import io, torch, timm
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from torchvision import transforms as T
from pydantic import BaseModel
from advice import get_advice, get_weather
from llm import ask_llm

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
    with torch.no_grad():
        p = torch.softmax(model(tf(img).unsqueeze(0)), 1)[0]
    top = p.topk(3)
    results = [{"disease": pretty(classes[i]), "confidence": round(v.item(), 3)}
               for v, i in zip(top.values, top.indices)]
    out = {"sure": results[0]["confidence"] >= THRESHOLD, "results": results}
    if out["sure"]:
        out["class"] = classes[top.indices[0]]
        out["advice"] = get_advice(classes[top.indices[0]])
        out["weather"] = get_weather()
    return out

class Ask(BaseModel):
    question: str
    disease: str | None = None

@app.post("/ask")
def ask(a: Ask):
    facts = None
    if a.disease:
        adv = get_advice(a.disease)
        facts = [adv["about"]] + adv["steps"]
    return {"answer": ask_llm(a.question, a.disease, facts)}

@app.get("/")
def home():
    return FileResponse("index.html")
