import torch
import tensorflow as tf
import numpy as np
import os
from brightness_learner import BrightnessNet

def verify_accuracy():
    print("🔬 Verifying TinyML Model Accuracy")
    print("=" * 50)
    
    # 1. Load PyTorch Model (Ground Truth)
    pt_model = BrightnessNet()
    if os.path.exists("brightness_model.pth"):
        checkpoint = torch.load("brightness_model.pth", map_location="cpu")
        pt_model.load_state_dict(checkpoint["model_state_dict"])
    pt_model.eval()
    
    # 2. Load TFLite Model (Quantized)
    tflite_path = "models/brightness_model_quantized.tflite"
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # 3. Run Comparison on Random Data
    n_samples = 100
    errors = []
    
    print(f"   Running inference on {n_samples} random samples...")
    
    for _ in range(n_samples):
        # Generate random input: [Hour(0-1), Motion(0/1), Light(0-1)]
        hour = np.random.random()
        motion = float(np.random.randint(0, 2))
        light = np.random.random()
        
        # PyTorch Inference
        pt_input = torch.tensor([[hour, motion, light]], dtype=torch.float32)
        with torch.no_grad():
            pt_out = pt_model(pt_input).item()
            
        # TFLite Inference
        tf_input = np.array([[hour, motion, light]], dtype=np.float32)
        interpreter.set_tensor(input_details[0]['index'], tf_input)
        interpreter.invoke()
        tf_out = interpreter.get_tensor(output_details[0]['index'])[0][0]
        
        errors.append(abs(pt_out - tf_out))
        
    # 4. Report Results
    mae = np.mean(errors)
    max_error = np.max(errors)
    
    print("\n📉 Accuracy Results")
    print("-" * 30)
    print(f"   Mean Absolute Error (MAE): {mae:.6f}")
    print(f"   Max Error:                 {max_error:.6f}")
    
    if mae < 0.05:
        print("\n✅ PASS: TFLite model matches PyTorch model within tolerance.")
    else:
        print("\n❌ FAIL: Significant accuracy loss detected.")
    print("=" * 50)

if __name__ == "__main__":
    verify_accuracy()
