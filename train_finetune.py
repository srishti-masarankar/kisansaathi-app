"""
Fine-tune combined_model.pth on field-style photos (free, runs on your laptop).

Folder layout (class folder names must match the model's class names exactly):
    data/train/<class_name>/*.jpg
    data/val/<class_name>/*.jpg
Tip: in data/train put your PlantDoc/field photos PLUS a small sample of PlantVillage
images, so the model improves on real photos without forgetting the lab-style ones.

Run:   python train_finetune.py --epochs 8
Output: combined_model_ft.pth  (same format as the original; the original file is never touched)
To use it, rename it to combined_model.pth (keep a backup of the old one).
"""
import argparse, torch, timm
from torch import nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms as T

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data")
ap.add_argument("--ckpt", default="combined_model.pth")
ap.add_argument("--out", default="combined_model_ft.pth")
ap.add_argument("--epochs", type=int, default=8)
ap.add_argument("--batch", type=int, default=16)
a = ap.parse_args()

dev = "cuda" if torch.cuda.is_available() else "cpu"
ckpt = torch.load(a.ckpt, map_location="cpu")
classes = ckpt["classes"]
model = timm.create_model("efficientnet_b0", num_classes=len(classes))
model.load_state_dict(ckpt["model"])
model.to(dev)

norm = T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
# augmentations that imitate messy real-field photos
train_tf = T.Compose([
    T.RandomResizedCrop(224, scale=(0.5, 1.0)), T.RandomHorizontalFlip(), T.RandomVerticalFlip(),
    T.RandomRotation(25), T.ColorJitter(0.4, 0.4, 0.4, 0.05),
    T.RandomApply([T.GaussianBlur(5, (0.1, 1.5))], p=0.3), T.RandomPerspective(0.2, p=0.3),
    T.ToTensor(), norm, T.RandomErasing(p=0.25)])
val_tf = T.Compose([T.Resize((224, 224)), T.ToTensor(), norm])

def load(split, tf):
    ds = datasets.ImageFolder(f"{a.data}/{split}", transform=tf)
    unknown = [c for c in ds.classes if c not in classes]
    if unknown:
        raise SystemExit(f"Folder names not in the model's classes: {unknown}\nExpected names like: {classes[:3]}")
    remap = {i: classes.index(c) for i, c in enumerate(ds.classes)}   # folder index -> model index
    ds.target_transform = lambda i: remap[i]
    return ds

tr, va = load("train", train_tf), load("val", val_tf)
counts = torch.bincount(torch.tensor([t for _, t in tr.samples]), minlength=len(tr.classes)).float()
w = (1.0 / counts)[[t for _, t in tr.samples]]            # balance rare classes
tl = DataLoader(tr, a.batch, sampler=WeightedRandomSampler(w, len(w)), num_workers=0)
vl = DataLoader(va, a.batch, num_workers=0)

head = [p for n, p in model.named_parameters() if n.startswith("classifier")]
rest = [p for n, p in model.named_parameters() if not n.startswith("classifier")]
opt = torch.optim.AdamW([{"params": rest, "lr": 1e-4}, {"params": head, "lr": 3e-4}], weight_decay=1e-4)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs)
lossf = nn.CrossEntropyLoss(label_smoothing=0.1)

def evaluate():
    model.eval(); ok = n = 0
    with torch.no_grad():
        for x, y in vl:
            ok += (model(x.to(dev)).argmax(1).cpu() == y).sum().item(); n += len(y)
    return ok / max(n, 1)

best = evaluate()
print(f"start val accuracy: {best:.3f}")
for ep in range(1, a.epochs + 1):
    model.train()
    for x, y in tl:
        opt.zero_grad(); lossf(model(x.to(dev)), y.to(dev)).backward(); opt.step()
    sched.step(); acc = evaluate()
    print(f"epoch {ep}/{a.epochs}  val accuracy {acc:.3f}")
    if acc > best:
        best = acc
        torch.save({"classes": classes, "model": {k: v.cpu() for k, v in model.state_dict().items()}}, a.out)
        print("  saved", a.out)
print(f"best val accuracy: {best:.3f}")
