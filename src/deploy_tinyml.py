import torch
import torch.nn as nn
import onnx
import tensorflow as tf
import os
import numpy as np

# Import the model definition
from brightness_learner import BrightnessNet

def deploy_tinyml():
    print("🚀 Starting TinyML Deployment Pipeline...")
    
    # 1. Load PyTorch Model
    model = BrightnessNet()
    # Load weights if available, otherwise use random init for demo
    if os.path.exists("brightness_model.pth"):
        checkpoint = torch.load("brightness_model.pth", map_location="cpu")
        model.load_state_dict(checkpoint["model_state_dict"])
        print("✓ Loaded trained PyTorch model")
    else:
        print("⚠️  No trained model found, using random weights for demonstration")
    
    model.eval()
    
    # 2. Export to ONNX
    dummy_input = torch.randn(1, 3) # Batch size 1, 3 inputs
    onnx_path = "models/brightness_model.onnx"
    os.makedirs("models", exist_ok=True)
    
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path,
        verbose=False,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"✓ Exported to ONNX: {onnx_path}")
    
    # 3. Convert ONNX to TensorFlow (SavedModel)
    # Note: Direct ONNX->TFLite is tricky. 
    # A robust path is: PyTorch -> ONNX -> TF SavedModel -> TFLite
    # We use onnx2tf (external tool) or simple TF implementation since the model is simple.
    # For this specific simple model (3 layers), it's easier to Re-implement in Keras for conversion
    # OR use onnx2tf. Given we can't easily install onnx2tf in this env, 
    # let's use the "Re-implement in Keras" strategy which is 100% reliable for simple MLPs.
    
    print("ℹ️  Converting to TFLite via Keras reconstruction (Reliable for Simple MLPs)...")
    
    # Extract weights from PyTorch
    fc1_w = model.fc1.weight.detach().numpy().T
    fc1_b = model.fc1.bias.detach().numpy()
    fc2_w = model.fc2.weight.detach().numpy().T
    fc2_b = model.fc2.bias.detach().numpy()
    fc3_w = model.fc3.weight.detach().numpy().T
    fc3_b = model.fc3.bias.detach().numpy()
    
    # Build Keras equivalent
    tf_model = tf.keras.Sequential([
        tf.keras.layers.Dense(16, activation='relu', input_shape=(3,)),
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    # Set weights
    tf_model.layers[0].set_weights([fc1_w, fc1_b])
    tf_model.layers[1].set_weights([fc2_w, fc2_b])
    tf_model.layers[2].set_weights([fc3_w, fc3_b])
    
    # 4. Convert to TFLite with Quantization
    converter = tf.lite.TFLiteConverter.from_keras_model(tf_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT] # Dynamic Range Quantization
    tflite_model = converter.convert()
    
    tflite_path = "models/brightness_model_quantized.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
        
    print(f"✓ Converted to TFLite (Quantized): {tflite_path}")
    
    # 5. Verify Size
    size_kb = os.path.getsize(tflite_path) / 1024
    print(f"📦 Final Model Size: {size_kb:.2f} KB")
    
    if size_kb < 100:
        print("✅ SUCCESS: Model is under 100KB (TinyML Ready!)")
    else:
        print("❌ WARNING: Model is too large")

if __name__ == "__main__":
    deploy_tinyml()
