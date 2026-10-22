import cv2
import numpy as np
import tensorflow as tf

model = None
labels = []

def load_labels():
    global labels
    with open("labels.txt") as f:
        labels = [line.strip().split(" ", 1)[1] for line in f if line.strip()]
    print("Labels loaded:", labels)

def load_model():
    global model
    if model is None:
        print("Loading model...")
        model = tf.keras.models.load_model("keras_model.h5", compile=False)
        print("Model loaded!")

def classify_image(frame):
    if model is None or not labels: return None
    
    # 1. Resize
    img = cv2.resize(frame, (224, 224))
    # 2. BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # 3. Normalize to [-1, 1]
    img = (img.astype(np.float32) / 127.5) - 1.0
    # 4. Add batch dimension
    img = np.expand_dims(img, axis=0)
    
    # 5. Predict
    preds = model.predict(img, verbose=0)[0]
    best_idx = int(np.argmax(preds))
    
    return {
        "class_name": labels[best_idx],
        "confidence": float(preds[best_idx])
    }