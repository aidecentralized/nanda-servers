import numpy as np
from PIL import Image, ImageFont, ImageDraw
import os
import time
import torch
import cv2
from torchvision.transforms.functional import to_pil_image

def plot_patch_overlay_on_image(patch_tensor, h, w, image_tensor):
    """
    Creates a beautiful heatmap overlay of patch contributions with a vertical colorbar.

    Args:
        patch_tensor (Tensor): Tensor of shape (num_patches,) or (1, num_patches)
        h (int): number of patches along height
        w (int): number of patches along width
        image_tensor (Tensor): Shape (1, 3, 224, 224) or (3, 224, 224)

    Returns:
        str: Path to saved heatmap image
    """
    # --- Normalize patch contributions ---
    patch_tensor = patch_tensor.squeeze()
    if isinstance(patch_tensor, torch.Tensor):
        patch_tensor = patch_tensor.detach().cpu().numpy()

    patch_tensor = (patch_tensor - patch_tensor.min()) / (patch_tensor.max() - patch_tensor.min() + 1e-8)
    heatmap = patch_tensor.reshape(h, w)

    # --- Resize heatmap to image size ---
    heatmap_resized = cv2.resize((heatmap * 255).astype(np.uint8), (224, 224), interpolation=cv2.INTER_CUBIC)
    colored_heatmap = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_MAGMA)

    # --- Original image prep ---
    if len(image_tensor.shape) == 4:
        image_tensor = image_tensor.squeeze(0)
    image_pil = to_pil_image(image_tensor)
    image_np = np.array(image_pil)

    if image_np.dtype != np.uint8:
        image_np = (image_np * 255).astype(np.uint8)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # --- Blend image + heatmap ---
    blended = cv2.addWeighted(image_bgr, 0.6, colored_heatmap, 0.4, 0)
    blended_rgb = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
    final_image = Image.fromarray(blended_rgb)

    # --- Create colorbar ---
    bar_height = 224
    bar_width = 50
    gradient = np.linspace(1.0, 0.0, bar_height)[:, None]
    gradient_img = np.uint8(gradient * 255)
    gradient_img = np.repeat(gradient_img, bar_width, axis=1)
    colorbar = cv2.applyColorMap(gradient_img, cv2.COLORMAP_MAGMA)
    colorbar_rgb = cv2.cvtColor(colorbar, cv2.COLOR_BGR2RGB)
    colorbar_pil = Image.fromarray(colorbar_rgb)

    # --- Draw labels on colorbar ---
    draw = ImageDraw.Draw(colorbar_pil)
    try:
        font = ImageFont.truetype("arial.ttf", size=12)
    except:
        font = ImageFont.load_default()

    label_steps = 6
    for i in range(label_steps + 1):
        value = 1.0 - (i / label_steps)
        y = int(i * (bar_height / label_steps)) - 6
        label = f"{value:.1f}"

        # Get text width/height safely
        try:
            # Preferred way (Pillow >= 8.0)
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            # Fallback
            text_width, _ = font.getsize(label)

        draw.text(((bar_width - text_width) / 2, y), label, fill="white", font=font)

    # --- Combine final image and colorbar ---
    spacing = 10
    total_width = final_image.width + spacing + colorbar_pil.width
    combined = Image.new("RGB", (total_width, 224), color=(0, 0, 0))
    combined.paste(final_image, (0, 0))
    combined.paste(colorbar_pil, (final_image.width + spacing, 0))

    # --- Save result ---
    timestamp = str(int(time.time()))
    path = f"overlay_{timestamp}.png"
    combined.save(path)
    return path
