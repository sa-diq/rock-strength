import cv2
import matplotlib.pyplot as plt
import numpy as np

# Load the legend image
img = cv2.imread('legend.png')
if img is None:
    raise FileNotFoundError('legend.png not found')

# 1. Crop to remove white margins (if any)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
coords = cv2.findNonZero(binary)
x, y, w, h = cv2.boundingRect(coords)
cropped = img[y:y+h, x:x+w]

# 2. Optionally, resize for easier clicking
cropped_resized = cv2.resize(cropped, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

# 3. Optionally, apply a slight blur to reduce noise (for color picking)
preprocessed = cv2.medianBlur(cropped_resized, 3)

# 4. Save the preprocessed legend image
cv2.imwrite('legend_preprocessed.png', preprocessed)

# 5. Show before/after for visual check
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
ax1.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
ax1.set_title('Original legend.png')
ax1.axis('off')
ax2.imshow(cv2.cvtColor(preprocessed, cv2.COLOR_BGR2RGB))
ax2.set_title('Preprocessed legend')
ax2.axis('off')
plt.tight_layout()
plt.show()
print('Saved preprocessed legend as legend_preprocessed.png')
