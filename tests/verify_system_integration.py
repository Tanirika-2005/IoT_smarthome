import unittest
import os
import shutil
import time
from brightness_learner import BrightnessLearner
# We can't easily test the MQTT loop without a broker, but we can test the logic flow
# by instantiating the learner and simulating the calls the controller would make.

class TestSmartHomeSystem(unittest.TestCase):
    
    def setUp(self):
        # Create a clean models directory
        os.makedirs("test_models", exist_ok=True)
        self.model_path = "test_models/test_room_model.pth"
        if os.path.exists(self.model_path):
            os.remove(self.model_path)
            
    def tearDown(self):
        # Cleanup
        if os.path.exists("test_models"):
            shutil.rmtree("test_models")

    def test_learner_initialization(self):
        """Test 1: Learner initializes correctly with PyTorch backend"""
        print("\n[Test 1] Learner Initialization")
        learner = BrightnessLearner(model_file=self.model_path)
        self.assertFalse(learner.is_trained)
        self.assertEqual(learner.sample_count, 0)
        print("✅ Learner initialized successfully")

    def test_prediction_before_training(self):
        """Test 2: Prediction works (heuristic) before training"""
        print("\n[Test 2] Pre-training Prediction")
        learner = BrightnessLearner(model_file=self.model_path)
        # Dark room + Motion = Should be bright (heuristic)
        pred = learner.predict(hour=20, motion=1, light_level=10)
        self.assertEqual(pred, 60.0) # Default heuristic
        print(f"✅ Heuristic prediction correct: {pred}")

    def test_learning_loop(self):
        """Test 3: Full Learning Loop (The Core Logic)"""
        print("\n[Test 3] Learning Loop")
        learner = BrightnessLearner(model_file=self.model_path)
        
        # Context: 8 PM, Motion, Dark
        h, m, l = 20, 1, 10
        target = 90.0
        
        # 1. Learn - Run a few times to ensure it learns well
        print("   Training on target 90.0...")
        for _ in range(3):
            learner.learn(h, m, l, target, user_id="tester")
        
        self.assertTrue(learner.is_trained)
        
        # 2. Predict
        pred = learner.predict(h, m, l)
        print(f"   Prediction after training: {pred:.2f}")
        
        # Should be significantly higher than 0 (random init usually ~50)
        self.assertTrue(pred > 50.0, "Prediction should be reasonable")
        print("✅ Learning update verified")

    def test_conflict_resolution(self):
        """Test 4: Multi-User Conflict Resolution"""
        print("\n[Test 4] Conflict Resolution")
        learner = BrightnessLearner(model_file=self.model_path)
        
        # Context
        h, m, l = 20, 1, 10
        context_key = learner._context_key(h, m, l)
        
        # Parent (Priority 2) wants 100
        # Child (Priority 1) wants 50
        
        # Simulate Child input first
        learner._resolve_conflict(context_key, h, m, l, "child", 50.0)
        
        # Simulate Parent input second
        resolved, conflict = learner._resolve_conflict(context_key, h, m, l, "parent", 100.0)
        
        print(f"   Child: 50, Parent: 100 -> Resolved: {resolved}")
        
        # Should favor Parent (100)
        self.assertEqual(resolved, 100.0)
        self.assertTrue(conflict)
        print("✅ Priority resolution verified (Parent wins)")

    def test_model_persistence(self):
        """Test 5: Save and Load"""
        print("\n[Test 5] Model Persistence")
        learner = BrightnessLearner(model_file=self.model_path)
        learner.learn(20, 1, 10, 80.0)
        learner.save_model()
        
        self.assertTrue(os.path.exists(self.model_path))
        
        # Load new instance
        learner2 = BrightnessLearner(model_file=self.model_path)
        self.assertTrue(learner2.is_trained)
        self.assertEqual(learner2.sample_count, 1)
        print("✅ Model saved and loaded successfully")

if __name__ == '__main__':
    unittest.main()
