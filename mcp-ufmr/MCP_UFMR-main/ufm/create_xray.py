from PIL import Image
img = Image.new("RGB", (224, 224), color=(128, 128, 128))
img.save("sample_xray.jpg")
