from .base_engine import BaseMLEngine


class RealMLEngine(BaseMLEngine):
    """
    Placeholder for future real-model mode.
    Keep the same public interface as MockMLEngine so no route/consumer changes are required.
    """

    def __init__(self):
        self.models = self._load_models()

    def _load_models(self):
        # Future implementation example:
        # import tensorflow as tf
        # return {
        #   "moteur": tf.keras.models.load_model("/app/models/moteur.h5"),
        #   ...
        # }
        raise NotImplementedError("Real model loading is not implemented yet.")

    def predict(self, machine, sensors):
        raise NotImplementedError("Real model prediction is not implemented yet.")