"""Grad-CAM heatmap for KisanSaathi. Free: needs only torch, numpy, Pillow."""
import io
import base64
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


def _jet(v):
    """Simple jet colormap, v in [0,1] -> RGB uint8."""
    r = np.clip(1.5 - np.abs(4 * v - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * v - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * v - 1), 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def _default_layer(model):
    # timm EfficientNet: last block before the head
    if hasattr(model, "blocks"):
        return model.blocks[-1]
    # torchvision style
    if hasattr(model, "features"):
        return model.features[-1]
    raise ValueError("Pass target_layer explicitly")


def gradcam_overlay(model, x, pil_img, class_idx=None, target_layer=None, alpha=0.45):
    """
    model     : your loaded classifier (eval mode is set here)
    x         : preprocessed tensor, shape (1, 3, H, W)
    pil_img   : original PIL image (RGB)
    class_idx : class to explain (default = top prediction)
    returns   : base64 PNG string of the heatmap overlaid on the leaf
    """
    model.eval()
    layer = target_layer or _default_layer(model)
    store = {}

    def fwd_hook(_, __, out):
        store["act"] = out
        out.register_hook(lambda g: store.__setitem__("grad", g))

    handle = layer.register_forward_hook(fwd_hook)
    try:
        with torch.enable_grad():
            x = x.clone().requires_grad_(True)
            logits = model(x)
            if class_idx is None:
                class_idx = int(logits.argmax(dim=1))
            model.zero_grad()
            logits[0, class_idx].backward()
    finally:
        handle.remove()

    act, grad = store["act"].detach(), store["grad"].detach()
    weights = grad.mean(dim=(2, 3), keepdim=True)
    cam = F.relu((weights * act).sum(dim=1, keepdim=True))
    cam = F.interpolate(cam, size=pil_img.size[::-1], mode="bilinear", align_corners=False)[0, 0]
    cam = cam.numpy()
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

    base = np.asarray(pil_img.convert("RGB"), dtype=np.float32)
    heat = _jet(cam).astype(np.float32)
    # tint only the strongly-activated regions, leave the rest of the photo clean
    a = (np.clip((cam - 0.35) / 0.65, 0, 1) * 0.7)[..., None]
    out = (base * (1 - a) + heat * a).clip(0, 255).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(out).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
