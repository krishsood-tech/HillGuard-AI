"""
HillGuard AI — ML adapters.

Replace DemoImageModel with a trained sklearn/pytorch artifact by implementing
`predict_image(path: Path) -> dict` with the same keys as ml_service.triage_image.

Replace risk estimation similarly; keep the public API in backend/app/ml_service.py.
"""

from pathlib import Path


class DemoImageModel:
    def predict(self, path: Path) -> dict:
        from app.ml_service import triage_image

        return triage_image(path)
