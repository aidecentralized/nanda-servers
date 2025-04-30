#!/bin/bash

#!/bin/bash

PORT=5057 # change if using a different port
IMG="test_xray.png"

if [ ! -f "$IMG" ]; then
    convert -size 224x224 xc:white "$IMG"  # Requires ImageMagick
fi

curl -X POST http://localhost:$PORT/functions/diagnose \
  -F "patient_id=test001" \
  -F "age=45" \
  -F "bp=120" \
  -F "hr=78" \
  -F "report=Patient reports persistent cough and fever." \
  -F "xray_image=@$IMG"
