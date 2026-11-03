import sys

# Prevent PyMuPDF 2.0+ from loading optional deep-learning ONNX layout models
# which require external ONNX/YAML weights that cause FileNotFoundError
if "pymupdf.layout" not in sys.modules:
    sys.modules["pymupdf.layout"] = None

