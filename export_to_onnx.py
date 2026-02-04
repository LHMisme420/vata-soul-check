import pickle
import numpy as np
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# Load your trained XGBoost model
with open("models/soul_model_v1.pkl", "rb") as f:
    model = pickle.load(f)

# Define input shape (from your features, e.g., 10 features)
initial_type = [('float_input', FloatTensorType([None, 10]))]  # adjust num features

# Convert to ONNX
onnx_model = convert_sklearn(model, initial_types=initial_type, target_opset=13)
with open("soul_model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

print("Exported to soul_model.onnx")