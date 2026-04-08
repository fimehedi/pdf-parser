## Preprocessing (deskew + dewarp + binarize)

### Why preprocessing matters
OCR accuracy on Bangla is highly sensitive to:
- skew/tilt (common in scanning)
- perspective distortion (camera/scanner geometry)
- noise and background texture

### Implemented steps (v1)
In `app/preprocessing/image_cleaner.py`:
- **Dewarp (simple)**: page contour detection + 4-point perspective transform
  - Corrects keystone/perspective (not full curved-page dewarping)
- **Denoise**: `fastNlMeansDenoising`
- **Binarize**: adaptive thresholding
- **Deskew**: rotation based on min-area rect on foreground pixels

### Signals captured
Each processed page emits:
- `blur_score` (Laplacian variance proxy)
- `deskew_angle_deg`
- `dewarp_applied` (bool)

### Next improvements
- Curved-page dewarping (textline-based) for bound books
- Illumination correction (shadow removal)
- Configurable preprocessing parameters per scan profile (e.g., 400 DPI TIFF)

