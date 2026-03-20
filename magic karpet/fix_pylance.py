# Quick test to verify cv2.rectangle exists
import cv2
import sys

print(f"OpenCV version: {cv2.__version__}")
print(f"cv2.rectangle exists: {hasattr(cv2, 'rectangle')}")

# Test if rectangle works
import numpy as np
test_img = np.zeros((100, 100, 3), dtype=np.uint8)
cv2.rectangle(test_img, (10, 10), (90, 90), (255, 255, 255), 2)
print("cv2.rectangle works correctly!")
