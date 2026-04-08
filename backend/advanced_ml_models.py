"""
Advanced ML Models for Early Warning System.
Includes XGBoost, LightGBM, Neural Networks, Ensemble Stacking, and more.
"""
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)
import pickle
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import advanced libraries with fallbacks
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available. Install with: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except Exception:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available. Install with: pip install lightgbm")

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except Exception:
    CATBOOST_AVAILABLE = False
    logger.warning("CatBoost not available. Install with: pip install catboost")

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. Install with: pip install tensorflow")

try:
    import optuna
    OPTUNA_AVAILABLE = True
except Exception:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not available. Install with: pip install optuna")

try:
    from sklearn.ensemble import IsolationForest, VotingClassifier
    from sklearn.linear_model import LogisticRegression
    ANOMALY_AVAILABLE = True
except Exception:
    ANOMALY_AVAILABLE = False


class AdvancedMLModels:
    """Advanced ML models for risk prediction."""
    
    def __init__(self):
        """Initialize advanced ML models."""
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)
        self.scaler = StandardScaler()
    
    def create_xgboost_model(
        self,
        n_estimators: int = 200,
        max_depth: int = 8,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42
    ):
        """Create optimized XGBoost model."""
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not available")
        
        return xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            eval_metric='mlogloss',
            use_label_encoder=False,
            tree_method='hist',  # Fast histogram-based method
            n_jobs=-1
        )
    
    def create_lightgbm_model(
        self,
        n_estimators: int = 200,
        max_depth: int = 8,
        learning_rate: float = 0.05,
        num_leaves: int = 31,
        feature_fraction: float = 0.8,
        bagging_fraction: float = 0.8,
        random_state: int = 42
    ):
        """Create optimized LightGBM model."""
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not available")
        
        return lgb.LGBMClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            num_leaves=num_leaves,
            feature_fraction=feature_fraction,
            bagging_fraction=bagging_fraction,
            random_state=random_state,
            n_jobs=-1,
            verbose=-1
        )
    
    def create_catboost_model(
        self,
        iterations: int = 200,
        depth: int = 8,
        learning_rate: float = 0.05,
        random_state: int = 42
    ):
        """Create optimized CatBoost model."""
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost not available")
        
        return cb.CatBoostClassifier(
            iterations=iterations,
            depth=depth,
            learning_rate=learning_rate,
            random_state=random_state,
            verbose=False,
            task_type='CPU'
        )
    
    def create_neural_network(
        self,
        input_dim: int,
        n_classes: int = 3,
        hidden_layers: List[int] = [128, 64, 32],
        dropout_rate: float = 0.3,
        learning_rate: float = 0.001
    ):
        """
        Create a neural-network style model for risk prediction.

        - If TensorFlow is available, returns a Keras model.
        - If TensorFlow is NOT available, returns a scikit-learn MLPClassifier fallback
          so the 'neural_network' model type still works end-to-end.
        """
        if not TENSORFLOW_AVAILABLE:
            return MLPClassifier(
                hidden_layer_sizes=tuple(hidden_layers),
                activation='relu',
                solver='adam',
                learning_rate_init=learning_rate,
                max_iter=500,
                random_state=42,
                early_stopping=True,
                n_iter_no_change=20,
            )
        
        model = Sequential()
        
        # Input layer
        model.add(Dense(hidden_layers[0], activation='relu', input_dim=input_dim))
        model.add(BatchNormalization())
        model.add(Dropout(dropout_rate))
        
        # Hidden layers
        for units in hidden_layers[1:]:
            model.add(Dense(units, activation='relu'))
            model.add(BatchNormalization())
            model.add(Dropout(dropout_rate))
        
        # Output layer
        if n_classes == 2:
            model.add(Dense(1, activation='sigmoid'))
            loss = 'binary_crossentropy'
        else:
            model.add(Dense(n_classes, activation='softmax'))
            loss = 'sparse_categorical_crossentropy'
        
        # Compile model
        optimizer = Adam(learning_rate=learning_rate)
        model.compile(
            optimizer=optimizer,
            loss=loss,
            metrics=['accuracy']
        )
        
        return model
    
    def create_ensemble_stacking(
        self,
        base_models: List[Any],
        meta_model: Optional[Any] = None
    ):
        """Create ensemble stacking model."""
        if meta_model is None:
            meta_model = LogisticRegression(max_iter=1000, random_state=42)
        
        return VotingClassifier(
            estimators=[(f'model_{i}', model) for i, model in enumerate(base_models)],
            voting='soft',
            n_jobs=-1
        )
    
    def train_xgboost(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Train XGBoost model with early stopping."""
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not available")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create model
        model = self.create_xgboost_model()
        
        # Train model.
        # NOTE: In newer xgboost versions (e.g. 3.x), sklearn .fit() no longer accepts
        # early_stopping_rounds / callbacks. We keep training simple and stable here.
        model.fit(
            X_train_scaled,
            y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False,
        )
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)
        
        metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)
        
        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': metrics,
            'model_type': 'xgboost',
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def train_lightgbm(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Train LightGBM model with early stopping."""
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not available")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create model
        model = self.create_lightgbm_model()
        
        # Train with early stopping
        model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(0)]
        )
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)
        
        metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)
        
        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': metrics,
            'model_type': 'lightgbm',
            'trained_at': datetime.utcnow().isoformat()
        }

    def train_catboost(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Train CatBoost model."""
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost not available")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Scale features (consistent with the rest of the pipeline)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Create model
        model = self.create_catboost_model(iterations=300)

        # Train
        model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = model.predict(X_test_scaled)
        # CatBoost sometimes returns shape (n,1)
        try:
            y_pred = np.array(y_pred).reshape(-1)
        except Exception:
            pass
        y_pred_proba = model.predict_proba(X_test_scaled)

        metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)

        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': metrics,
            'model_type': 'catboost',
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def train_neural_network(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Train a neural network model.

        If TensorFlow is unavailable, trains a scikit-learn MLPClassifier fallback and
        returns model_type 'neural_network_sklearn' (pickle-safe, loadable everywhere).
        """
        if not TENSORFLOW_AVAILABLE:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Create + train sklearn MLP
            n_classes = len(np.unique(y))
            model = self.create_neural_network(
                input_dim=X_train_scaled.shape[1],
                n_classes=n_classes
            )
            model.fit(X_train_scaled, y_train)

            # Evaluate
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)
            metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)

            return {
                'model': model,
                'scaler': self.scaler,
                'metrics': metrics,
                'model_type': 'neural_network_sklearn',
                'trained_at': datetime.utcnow().isoformat()
            }
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Determine number of classes
        n_classes = len(np.unique(y))
        
        # Create model
        model = self.create_neural_network(
            input_dim=X_train_scaled.shape[1],
            n_classes=n_classes
        )
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7)
        ]
        
        # Train model
        history = model.fit(
            X_train_scaled, y_train,
            validation_data=(X_test_scaled, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=0
        )
        
        # Evaluate
        y_pred_proba = model.predict(X_test_scaled, verbose=0)
        if n_classes == 2:
            y_pred = (y_pred_proba > 0.5).astype(int).flatten()
        else:
            y_pred = np.argmax(y_pred_proba, axis=1)
        
        metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)
        metrics['training_history'] = {
            'loss': [float(x) for x in history.history['loss']],
            'val_loss': [float(x) for x in history.history['val_loss']],
            'accuracy': [float(x) for x in history.history['accuracy']],
            'val_accuracy': [float(x) for x in history.history['val_accuracy']]
        }
        
        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': metrics,
            'model_type': 'neural_network',
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def train_ensemble(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Train ensemble of multiple models."""
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create base models
        base_models = []
        
        if XGBOOST_AVAILABLE:
            try:
                xgb_model = self.create_xgboost_model(n_estimators=100)
                base_models.append(('xgb', xgb_model))
            except:
                pass
        
        if LIGHTGBM_AVAILABLE:
            try:
                lgb_model = self.create_lightgbm_model(n_estimators=100)
                base_models.append(('lgb', lgb_model))
            except:
                pass
        
        if CATBOOST_AVAILABLE:
            try:
                cat_model = self.create_catboost_model(iterations=100)
                base_models.append(('cat', cat_model))
            except:
                pass
        
        if not base_models:
            raise ValueError("No advanced models available. Install XGBoost, LightGBM, or CatBoost")
        
        # Create ensemble
        ensemble = VotingClassifier(
            estimators=base_models,
            voting='soft',
            n_jobs=-1
        )
        
        # Train ensemble
        ensemble.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = ensemble.predict(X_test_scaled)
        y_pred_proba = ensemble.predict_proba(X_test_scaled)
        
        metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)
        
        return {
            'model': ensemble,
            'scaler': self.scaler,
            'metrics': metrics,
            'model_type': 'ensemble',
            'base_models': [name for name, _ in base_models],
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def optimize_hyperparameters(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_type: str = 'xgboost',
        n_trials: int = 50,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Optimize hyperparameters using Optuna."""
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna not available")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        def objective(trial):
            if model_type == 'xgboost':
                model = xgb.XGBClassifier(
                    n_estimators=trial.suggest_int('n_estimators', 100, 500),
                    max_depth=trial.suggest_int('max_depth', 3, 10),
                    learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    subsample=trial.suggest_float('subsample', 0.6, 1.0),
                    colsample_bytree=trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    random_state=random_state,
                    eval_metric='mlogloss',
                    use_label_encoder=False,
                    n_jobs=-1
                )
            elif model_type == 'lightgbm':
                model = lgb.LGBMClassifier(
                    n_estimators=trial.suggest_int('n_estimators', 100, 500),
                    max_depth=trial.suggest_int('max_depth', 3, 10),
                    learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    num_leaves=trial.suggest_int('num_leaves', 10, 50),
                    feature_fraction=trial.suggest_float('feature_fraction', 0.6, 1.0),
                    bagging_fraction=trial.suggest_float('bagging_fraction', 0.6, 1.0),
                    random_state=random_state,
                    n_jobs=-1,
                    verbose=-1
                )
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Cross-validation
            cv_scores = []
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
            for train_idx, val_idx in skf.split(X_train_scaled, y_train):
                X_tr, X_val = X_train_scaled[train_idx], X_train_scaled[val_idx]
                y_tr, y_val = y_train[train_idx], y_train[val_idx]
                
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                score = f1_score(y_val, y_pred, average='weighted')
                cv_scores.append(score)
            
            return np.mean(cv_scores)
        
        # Run optimization
        study = optuna.create_study(direction='maximize', study_name=f'{model_type}_optimization')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        # Train best model
        best_params = study.best_params
        if model_type == 'xgboost':
            best_model = xgb.XGBClassifier(**best_params, random_state=random_state, n_jobs=-1)
        elif model_type == 'lightgbm':
            best_model = lgb.LGBMClassifier(**best_params, random_state=random_state, n_jobs=-1, verbose=-1)
        
        best_model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = best_model.predict(X_test_scaled)
        y_pred_proba = best_model.predict_proba(X_test_scaled)
        metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)
        
        return {
            'model': best_model,
            'scaler': self.scaler,
            'metrics': metrics,
            'model_type': f'{model_type}_optimized',
            'best_params': best_params,
            'best_trial_value': study.best_value,
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def detect_anomalies(
        self,
        X: np.ndarray,
        contamination: float = 0.1,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies using Isolation Forest."""
        if not ANOMALY_AVAILABLE:
            raise ImportError("Isolation Forest not available")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Create and fit isolation forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )
        
        anomalies = iso_forest.fit_predict(X_scaled)
        anomaly_scores = iso_forest.score_samples(X_scaled)
        
        # Convert: -1 (anomaly) -> 1, 1 (normal) -> 0
        anomaly_labels = (anomalies == -1).astype(int)
        
        return anomaly_labels, anomaly_scores
    
    def _calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate comprehensive metrics."""
        metrics = {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0)),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
        }
        
        # ROC-AUC
        try:
            n_classes = len(np.unique(y_true))
            if n_classes == 2:
                metrics['roc_auc'] = float(roc_auc_score(y_true, y_pred_proba[:, 1]))
            else:
                metrics['roc_auc'] = float(roc_auc_score(
                    y_true, y_pred_proba, multi_class='ovr', average='weighted'
                ))
        except:
            metrics['roc_auc'] = 0.0
        
        return metrics
    
    def save_model(self, model_data: Dict[str, Any], version: str = "advanced") -> str:
        """Save trained model."""
        model_path = os.path.join(self.models_dir, f"advanced_model_{version}.pkl")
        
        # Handle TensorFlow models separately
        if model_data['model_type'] == 'neural_network':
            # Save Keras model separately
            keras_path = os.path.join(self.models_dir, f"neural_network_{version}.h5")
            model_data['model'].save(keras_path)
            model_data['model_path'] = keras_path
            # Don't pickle Keras model
            model_to_save = {k: v for k, v in model_data.items() if k != 'model'}
        else:
            model_to_save = model_data
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_to_save, f)
        
        logger.info(f"Advanced model saved to {model_path}")
        return model_path


# Global instance
advanced_ml = AdvancedMLModels()
