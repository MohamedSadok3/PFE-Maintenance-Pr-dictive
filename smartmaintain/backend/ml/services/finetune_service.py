"""
FineTuneService — Gestion des jobs de fine-tuning pour SmartMaintain
=====================================================================
Implémente un système de jobs asynchrones pour réentraîner les modèles
XGBoost depuis un fichier CSV uploadé par l'utilisateur.

Chaque job est exécuté dans un thread séparé et son état est stocké
en mémoire (dict thread-safe).  Pour une production robuste, remplacer
par une file de tâches persistante (Celery + Redis, RQ, etc.).
"""

import csv
import io
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Stockage en mémoire des jobs (remplacer par Redis ou DB en prod)
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()

MODELS_DIR = Path("/app/models")

# Statuts possibles d'un job
STATUS_PENDING   = "pending"
STATUS_RUNNING   = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED    = "failed"

SUPPORTED_MACHINES = {"moteur", "pompe", "compresseur", "echangeur"}


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _update_job(job_id: str, **kwargs) -> None:
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


def _get_job(job_id: str) -> Optional[dict]:
    with _jobs_lock:
        return dict(_jobs[job_id]) if job_id in _jobs else None


def _create_job(machine: str, model_name: str) -> str:
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id":     job_id,
            "machine":    machine,
            "model_name": model_name,
            "status":     STATUS_PENDING,
            "progress":   0,
            "message":    "En attente de démarrage...",
            "accuracy":   None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
        }
    return job_id


# ---------------------------------------------------------------------------
# Worker de réentraînement
# ---------------------------------------------------------------------------

def _train_worker(job_id: str, machine: str, model_name: str, csv_bytes: bytes) -> None:
    """
    Exécuté dans un thread séparé.
    Réentraîne le modèle XGBoost depuis les données CSV fournies.
    """
    try:
        _update_job(job_id, status=STATUS_RUNNING, progress=5,
                    message="Chargement des données...")

        # ── 1. Parser le CSV ──────────────────────────────────────────────
        try:
            import pandas as pd
            df = pd.read_csv(io.BytesIO(csv_bytes))
        except Exception as exc:
            raise ValueError(f"Impossible de lire le CSV : {exc}") from exc

        required_cols = {"label"}
        if not required_cols.issubset(df.columns):
            raise ValueError(
                f"Le CSV doit contenir une colonne 'label'. "
                f"Colonnes trouvées : {list(df.columns)}"
            )

        feature_cols = [c for c in df.columns if c != "label"]
        if len(feature_cols) < 1:
            raise ValueError("Le CSV doit contenir au moins une colonne de feature.")

        X = df[feature_cols].values
        y = df["label"].values

        _update_job(job_id, progress=20,
                    message=f"Données chargées : {len(df)} lignes, {len(feature_cols)} features.")

        # ── 2. Entraîner ──────────────────────────────────────────────────
        try:
            from sklearn.preprocessing import LabelEncoder, StandardScaler
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import xgboost as xgb
            import joblib
        except ImportError as exc:
            raise RuntimeError(
                f"Dépendance manquante pour l'entraînement : {exc}. "
                "Installez les packages listés dans requirements_ml.txt."
            ) from exc

        _update_job(job_id, progress=30, message="Encodage des labels...")
        le = LabelEncoder()
        y_enc = le.fit_transform(y)

        _update_job(job_id, progress=40, message="Normalisation des features...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        _update_job(job_id, progress=50, message="Séparation train/test (80/20)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_enc, test_size=0.2, random_state=42, stratify=y_enc
        )

        _update_job(job_id, progress=60, message="Entraînement XGBoost...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)

        _update_job(job_id, progress=80, message="Évaluation sur le jeu de test...")
        y_pred = model.predict(X_test)
        accuracy = float(accuracy_score(y_test, y_pred))

        # ── 3. Sauvegarder ────────────────────────────────────────────────
        _update_job(job_id, progress=90, message="Sauvegarde des artefacts...")
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        model_path   = MODELS_DIR / f"{machine}_xgb.pkl"
        scaler_path  = MODELS_DIR / f"{machine}_scaler.pkl"
        le_path      = MODELS_DIR / f"{machine}_label_encoder.pkl"
        meta_path    = MODELS_DIR / f"{machine}_metadata.json"

        joblib.dump(model,  model_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(le,     le_path)

        metadata = {
            "machine":      machine,
            "model_name":   model_name,
            "accuracy":     round(accuracy, 4),
            "n_samples":    len(df),
            "n_features":   len(feature_cols),
            "feature_names": feature_cols,
            "classes":      list(le.classes_),
            "trained_at":   datetime.now(timezone.utc).isoformat(),
            "job_id":       job_id,
        }
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        _update_job(
            job_id,
            status=STATUS_COMPLETED,
            progress=100,
            accuracy=round(accuracy, 4),
            message=f"Modèle entraîné avec succès. Accuracy : {accuracy:.2%}",
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        logger.info(
            "[FineTuneService] Job %s terminé — machine=%s accuracy=%.4f",
            job_id, machine, accuracy,
        )

    except Exception as exc:
        logger.error("[FineTuneService] Job %s échoué : %s", job_id, exc)
        _update_job(
            job_id,
            status=STATUS_FAILED,
            progress=0,
            message=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )


# ---------------------------------------------------------------------------
# Service public
# ---------------------------------------------------------------------------

class FineTuneService:
    """Gestion des jobs de réentraînement de modèles."""

    def submit_job(self, machine: str, model_name: str, csv_bytes: bytes) -> dict:
        """
        Soumet un job de réentraînement.
        Retourne immédiatement avec le job_id ; l'entraînement tourne en arrière-plan.
        """
        machine = (machine or "").lower()
        if machine not in SUPPORTED_MACHINES:
            return {"error": f"Machine non supportée. Valeurs acceptées : {sorted(SUPPORTED_MACHINES)}"}, 400

        if not model_name or not model_name.strip():
            return {"error": "model_name est requis."}, 400

        if not csv_bytes:
            return {"error": "Un fichier CSV de données d'entraînement est requis."}, 400

        job_id = _create_job(machine, model_name.strip())

        thread = threading.Thread(
            target=_train_worker,
            args=(job_id, machine, model_name.strip(), csv_bytes),
            daemon=True,
            name=f"finetune-{machine}-{job_id[:8]}",
        )
        thread.start()

        logger.info(
            "[FineTuneService] Job soumis — job_id=%s machine=%s model=%s",
            job_id, machine, model_name,
        )
        return _get_job(job_id), 202

    def get_job_status(self, job_id: str) -> dict:
        """Retourne l'état courant d'un job."""
        job = _get_job(job_id)
        if not job:
            return {"error": "Job introuvable."}, 404
        return job, 200

    def list_jobs(self) -> dict:
        """Liste tous les jobs (les plus récents en premier)."""
        with _jobs_lock:
            jobs = sorted(_jobs.values(), key=lambda j: j["created_at"], reverse=True)
        return {"jobs": list(jobs)}, 200
