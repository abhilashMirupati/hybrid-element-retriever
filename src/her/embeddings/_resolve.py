# PLACE THIS FILE AT: src/her/embeddings/_resolve.py

import onnxruntime as ort

class EmbeddingResolver:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path)

    def embed(self, tokens):
        inputs = {self.session.get_inputs()[0].name: tokens}
        return self.session.run(None, inputs)[0]
