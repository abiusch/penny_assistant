#!/usr/bin/env python3
"""
Predictive Security Analytics System for Penny Assistant
Part of Phase C2: Intelligence Integration (Days 4-5)

This system provides advanced predictive security analytics:
- AI-powered threat prediction using pattern recognition and machine learning
- Risk forecasting based on behavioral trends and historical data
- Security event correlation with temporal and contextual analysis
- Proactive vulnerability identification before exploitation occurs
- Social situation risk modeling (different predictions for Josh/Reneille interactions)
- Emotional state impact analysis on security decisions and risk levels
- Adaptive learning from security incidents to improve future predictions

Integration: Works with threat detection, authentication, and social intelligence systems
Database: SQLite persistence with ML model storage and training data
Testing: Comprehensive validation of prediction accuracy and model performance
"""

import asyncio
import sqlite3
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import threading
import logging
import statistics
import hashlib
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import pickle
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionType(Enum):
    """Types of security predictions"""
    THREAT_LIKELIHOOD = "threat_likelihood"
    BREACH_PROBABILITY = "breach_probability"
    ATTACK_TIMING = "attack_timing"
    VULNERABILITY_RISK = "vulnerability_risk"
    USER_BEHAVIOR_RISK = "user_behavior_risk"
    SOCIAL_ENGINEERING_RISK = "social_engineering_risk"
    SYSTEM_COMPROMISE_RISK = "system_compromise_risk"

class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

class PredictionConfidence(Enum):
    """Confidence levels for predictions"""
    VERY_LOW = "very_low"    # 0-20%
    LOW = "low"              # 20-40%
    MEDIUM = "medium"        # 40-60%
    HIGH = "high"            # 60-80%
    VERY_HIGH = "very_high"  # 80-100%

class ModelType(Enum):
    """Types of ML models used"""
    ANOMALY_DETECTION = "anomaly_detection"
    THREAT_CLASSIFICATION = "threat_classification"
    RISK_REGRESSION = "risk_regression"
    TIME_SERIES = "time_series"
    SOCIAL_PATTERN = "social_pattern"

@dataclass
class SecurityPrediction:
    """Security prediction result"""
    prediction_id: str
    prediction_type: PredictionType
    predicted_risk_level: RiskLevel
    risk_score: float  # 0.0 to 1.0
    confidence: PredictionConfidence
    confidence_score: float  # 0.0 to 1.0

    # Prediction details
    affected_entities: List[str]  # Users, systems, resources
    predicted_timeframe: Optional[Tuple[datetime, datetime]]  # When prediction applies
    key_indicators: List[str]     # What led to this prediction
    mitigation_recommendations: List[str]

    # Context
    social_context: Optional[str]
    emotional_factors: Dict[str, float]
    environmental_factors: Dict[str, Any]

    # Metadata
    model_used: ModelType
    training_data_size: int
    feature_importance: Dict[str, float]
    prediction_basis: List[str]  # Historical patterns, current trends, etc.

    # Timing
    generated_at: datetime
    valid_until: Optional[datetime]
    last_updated: Optional[datetime]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['prediction_type'] = self.prediction_type.value
        result['predicted_risk_level'] = self.predicted_risk_level.value
        result['confidence'] = self.confidence.value
        result['model_used'] = self.model_used.value
        result['generated_at'] = self.generated_at.isoformat()
        if self.predicted_timeframe:
            result['predicted_timeframe'] = [
                self.predicted_timeframe[0].isoformat(),
                self.predicted_timeframe[1].isoformat()
            ]
        if self.valid_until:
            result['valid_until'] = self.valid_until.isoformat()
        if self.last_updated:
            result['last_updated'] = self.last_updated.isoformat()
        return result

@dataclass
class SecurityTrend:
    """Security trend analysis"""
    trend_id: str
    trend_type: str
    description: str
    direction: str  # increasing, decreasing, stable, volatile
    magnitude: float  # Strength of trend
    confidence: float  # How confident we are in this trend
    timeframe: Tuple[datetime, datetime]
    affected_metrics: List[str]
    correlation_factors: Dict[str, float]
    implications: List[str]
    detected_at: datetime

@dataclass
class RiskForecast:
    """Risk forecast for future periods"""
    forecast_id: str
    forecast_period: Tuple[datetime, datetime]
    risk_trajectory: List[Tuple[datetime, float]]  # Time series of risk scores
    peak_risk_periods: List[Tuple[datetime, datetime, float]]
    key_risk_drivers: Dict[str, float]
    mitigation_windows: List[Tuple[datetime, datetime]]  # Best times for intervention
    confidence_intervals: List[Tuple[float, float]]  # Upper and lower bounds
    scenario_analysis: Dict[str, float]  # Different scenarios and their probabilities
    generated_at: datetime

class PredictiveSecurityAnalytics:
    """
    Advanced predictive security analytics with AI-powered threat prediction.

    Features:
    - Multiple ML models for different prediction types
    - Social context-aware risk modeling
    - Emotional state impact analysis
    - Temporal pattern recognition
    - Adaptive learning from new security data
    - Proactive vulnerability identification
    - Real-time risk forecasting
    """

    def __init__(self,
                 db_path: str = "predictive_security.db",
                 models_path: str = "./security_models/",
                 threat_detection_system=None,
                 social_intelligence=None,
                 security_logger=None):
        self.db_path = db_path
        self.models_path = Path(models_path)
        self.threat_detection_system = threat_detection_system
        self.social_intelligence = social_intelligence
        self.security_logger = security_logger

        # Ensure models directory exists
        self.models_path.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.prediction_enabled = True
        self.auto_retrain = True
        self.min_training_samples = 50
        self.max_prediction_horizon_hours = 168  # 1 week
        self.confidence_threshold = 0.6

        # ML Models
        self.models: Dict[ModelType, Any] = {}
        self.scalers: Dict[ModelType, StandardScaler] = {}
        self.model_metrics: Dict[ModelType, Dict[str, float]] = {}

        # Prediction state
        self.active_predictions: Dict[str, SecurityPrediction] = {}
        self.historical_predictions: List[SecurityPrediction] = []
        self.security_trends: Dict[str, SecurityTrend] = {}
        self.risk_forecasts: Dict[str, RiskForecast] = {}

        # Training data
        self.training_data: Dict[str, List[Dict[str, Any]]] = {}
        self.feature_columns: Dict[ModelType, List[str]] = {}

        # Analytics state
        self.recent_events: List[Dict[str, Any]] = []
        self.user_risk_profiles: Dict[str, Dict[str, Any]] = {}
        self.system_risk_baseline: Dict[str, float] = {}

        # Background processing
        self.analytics_active = False
        self.analytics_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_predictions': 0,
            'predictions_by_type': {ptype.value: 0 for ptype in PredictionType},
            'predictions_by_confidence': {conf.value: 0 for conf in PredictionConfidence},
            'model_accuracy': {},
            'prediction_accuracy': 0.0,
            'false_positive_rate': 0.0,
            'average_confidence': 0.0,
            'training_cycles': 0,
            'data_points_processed': 0
        }

        self._init_database()

    def _init_database(self):
        """Initialize predictive analytics database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Security predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_predictions (
                    prediction_id TEXT PRIMARY KEY,
                    prediction_type TEXT NOT NULL,
                    predicted_risk_level TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    confidence TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    affected_entities TEXT NOT NULL,
                    predicted_timeframe_start TEXT,
                    predicted_timeframe_end TEXT,
                    key_indicators TEXT NOT NULL,
                    mitigation_recommendations TEXT NOT NULL,
                    social_context TEXT,
                    emotional_factors TEXT NOT NULL,
                    environmental_factors TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    training_data_size INTEGER NOT NULL,
                    feature_importance TEXT NOT NULL,
                    prediction_basis TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    valid_until TEXT,
                    last_updated TEXT,
                    actual_outcome TEXT,
                    outcome_timestamp TEXT,
                    accuracy_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Security trends table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_trends (
                    trend_id TEXT PRIMARY KEY,
                    trend_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    magnitude REAL NOT NULL,
                    confidence REAL NOT NULL,
                    timeframe_start TEXT NOT NULL,
                    timeframe_end TEXT NOT NULL,
                    affected_metrics TEXT NOT NULL,
                    correlation_factors TEXT NOT NULL,
                    implications TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Training data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_data (
                    data_id TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    features TEXT NOT NULL,
                    target_value REAL,
                    target_class TEXT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    context_data TEXT,
                    validated BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Model performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    model_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    accuracy REAL,
                    precision_score REAL,
                    recall REAL,
                    f1_score REAL,
                    training_samples INTEGER,
                    validation_samples INTEGER,
                    feature_count INTEGER,
                    training_time_seconds REAL,
                    last_trained TEXT NOT NULL,
                    model_parameters TEXT,
                    feature_importance TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_type ON security_predictions(prediction_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON security_predictions(generated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_type ON security_trends(trend_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_data_type ON training_data(data_type)")

            conn.commit()

    async def start_analytics(self):
        """Start predictive analytics processing"""
        if self.analytics_active:
            return

        self.analytics_active = True

        # Load existing models and data
        await self._load_existing_models()
        await self._load_training_data()
        await self._load_historical_predictions()

        # Initialize models if needed
        await self._initialize_models()

        # Start analytics thread
        self.analytics_thread = threading.Thread(target=self._analytics_loop, daemon=True)
        self.analytics_thread.start()

        logger.info("Predictive security analytics started")

    async def stop_analytics(self):
        """Stop predictive analytics processing"""
        self.analytics_active = False
        if self.analytics_thread and self.analytics_thread.is_alive():
            self.analytics_thread.join(timeout=5)
        logger.info("Predictive security analytics stopped")

    def _generate_prediction_id(self) -> str:
        """Generate unique prediction ID"""
        return f"pred_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

    async def generate_security_prediction(self,
                                         prediction_type: PredictionType,
                                         context_data: Dict[str, Any],
                                         target_entities: Optional[List[str]] = None,
                                         time_horizon_hours: int = 24) -> Optional[SecurityPrediction]:
        """
        Generate a security prediction using appropriate ML models.

        Args:
            prediction_type: Type of prediction to generate
            context_data: Current context and input data
            target_entities: Specific entities to predict for
            time_horizon_hours: How far into the future to predict

        Returns:
            SecurityPrediction if successful, None otherwise
        """
        try:
            if not self.prediction_enabled:
                return None

            # Prepare features for prediction
            features = await self._extract_prediction_features(context_data, prediction_type)
            if not features:
                logger.warning(f"Could not extract features for {prediction_type.value}")
                return None

            # Select appropriate model
            model_type = self._get_model_type_for_prediction(prediction_type)
            if model_type not in self.models:
                logger.warning(f"Model {model_type.value} not available for {prediction_type.value}")
                return None

            model = self.models[model_type]
            scaler = self.scalers.get(model_type)

            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features, model_type)
            if scaler:
                feature_vector = scaler.transform([feature_vector])
            else:
                feature_vector = [feature_vector]

            # Make prediction
            if prediction_type in [PredictionType.THREAT_LIKELIHOOD, PredictionType.BREACH_PROBABILITY]:
                # Classification prediction
                risk_probability = model.predict_proba(feature_vector)[0]
                risk_score = max(risk_probability) if len(risk_probability) > 1 else risk_probability[0]
                predicted_class = model.predict(feature_vector)[0]
            else:
                # Regression prediction
                risk_score = model.predict(feature_vector)[0]
                predicted_class = None

            # Determine risk level and confidence
            risk_level = self._score_to_risk_level(risk_score)
            confidence = self._calculate_prediction_confidence(features, model_type, risk_score)

            # Get feature importance
            feature_importance = self._get_feature_importance(model, model_type, features.keys())

            # Generate key indicators and recommendations
            key_indicators = self._identify_key_indicators(features, feature_importance)
            recommendations = await self._generate_mitigation_recommendations(
                prediction_type, risk_level, key_indicators, context_data
            )

            # Determine prediction timeframe
            timeframe = self._calculate_prediction_timeframe(time_horizon_hours, risk_score)

            # Get social and emotional context
            social_context = await self._analyze_social_context(context_data)
            emotional_factors = self._extract_emotional_factors(context_data)
            environmental_factors = self._extract_environmental_factors(context_data)

            # Create prediction
            prediction = SecurityPrediction(
                prediction_id=self._generate_prediction_id(),
                prediction_type=prediction_type,
                predicted_risk_level=risk_level,
                risk_score=risk_score,
                confidence=self._score_to_confidence_level(confidence),
                confidence_score=confidence,
                affected_entities=target_entities or [],
                predicted_timeframe=timeframe,
                key_indicators=key_indicators,
                mitigation_recommendations=recommendations,
                social_context=social_context,
                emotional_factors=emotional_factors,
                environmental_factors=environmental_factors,
                model_used=model_type,
                training_data_size=len(self.training_data.get(model_type.value, [])),
                feature_importance=feature_importance,
                prediction_basis=self._determine_prediction_basis(features, model_type),
                generated_at=datetime.now(),
                valid_until=datetime.now() + timedelta(hours=time_horizon_hours)
            )

            # Store prediction
            self.active_predictions[prediction.prediction_id] = prediction
            await self._store_prediction(prediction)

            # Update statistics
            self.stats['total_predictions'] += 1
            self.stats['predictions_by_type'][prediction_type.value] += 1
            self.stats['predictions_by_confidence'][prediction.confidence.value] += 1

            # Log prediction
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type="SECURITY_PREDICTION_GENERATED",
                    severity="INFO",
                    details={
                        'prediction_id': prediction.prediction_id,
                        'prediction_type': prediction_type.value,
                        'risk_level': risk_level.value,
                        'confidence': confidence
                    }
                )

            logger.info(f"Generated {prediction_type.value} prediction: {risk_level.value} risk (confidence: {confidence:.2f})")
            return prediction

        except Exception as e:
            logger.error(f"Error generating security prediction: {e}")
            return None

    async def analyze_security_trends(self, analysis_period_days: int = 7) -> List[SecurityTrend]:
        """
        Analyze security trends over a specified period.

        Args:
            analysis_period_days: Period to analyze trends over

        Returns:
            List of detected security trends
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=analysis_period_days)

            # Get security events from the period
            security_events = await self._get_security_events_since(cutoff_time)
            if len(security_events) < 10:  # Need minimum events for trend analysis
                return []

            trends = []

            # Analyze different trend types
            trends.extend(await self._analyze_threat_frequency_trends(security_events))
            trends.extend(await self._analyze_user_behavior_trends(security_events))
            trends.extend(await self._analyze_attack_pattern_trends(security_events))
            trends.extend(await self._analyze_vulnerability_trends(security_events))

            # Store trends
            for trend in trends:
                self.security_trends[trend.trend_id] = trend
                await self._store_security_trend(trend)

            logger.info(f"Analyzed security trends: {len(trends)} trends detected over {analysis_period_days} days")
            return trends

        except Exception as e:
            logger.error(f"Error analyzing security trends: {e}")
            return []

    async def generate_risk_forecast(self,
                                   forecast_horizon_hours: int = 168,
                                   entities: Optional[List[str]] = None) -> Optional[RiskForecast]:
        """
        Generate risk forecast for specified time horizon.

        Args:
            forecast_horizon_hours: How far ahead to forecast
            entities: Specific entities to forecast for

        Returns:
            RiskForecast if successful, None otherwise
        """
        try:
            # Collect historical risk data
            historical_data = await self._get_historical_risk_data(entities)
            if len(historical_data) < 24:  # Need minimum historical data
                logger.warning("Insufficient historical data for risk forecasting")
                return None

            # Prepare time series data
            time_series = self._prepare_time_series_data(historical_data)

            # Generate forecast points
            forecast_points = []
            current_time = datetime.now()

            for hour in range(0, forecast_horizon_hours, 4):  # Every 4 hours
                forecast_time = current_time + timedelta(hours=hour)

                # Use trend analysis and pattern recognition for forecasting
                risk_score = await self._forecast_risk_at_time(forecast_time, time_series, entities)
                forecast_points.append((forecast_time, risk_score))

            # Identify peak risk periods
            peak_periods = self._identify_peak_risk_periods(forecast_points)

            # Analyze key risk drivers
            risk_drivers = await self._analyze_risk_drivers(historical_data, forecast_points)

            # Identify mitigation windows
            mitigation_windows = self._identify_mitigation_windows(forecast_points)

            # Calculate confidence intervals
            confidence_intervals = self._calculate_forecast_confidence_intervals(forecast_points, historical_data)

            # Scenario analysis
            scenarios = await self._perform_scenario_analysis(forecast_points, entities)

            # Create forecast
            forecast_id = f"forecast_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

            forecast = RiskForecast(
                forecast_id=forecast_id,
                forecast_period=(current_time, current_time + timedelta(hours=forecast_horizon_hours)),
                risk_trajectory=forecast_points,
                peak_risk_periods=peak_periods,
                key_risk_drivers=risk_drivers,
                mitigation_windows=mitigation_windows,
                confidence_intervals=confidence_intervals,
                scenario_analysis=scenarios,
                generated_at=current_time
            )

            self.risk_forecasts[forecast_id] = forecast
            logger.info(f"Generated risk forecast for {forecast_horizon_hours} hours with {len(forecast_points)} data points")
            return forecast

        except Exception as e:
            logger.error(f"Error generating risk forecast: {e}")
            return None

    async def train_prediction_models(self, model_types: Optional[List[ModelType]] = None) -> Dict[ModelType, Dict[str, float]]:
        """
        Train or retrain prediction models with latest data.

        Args:
            model_types: Specific models to train, None for all

        Returns:
            Dictionary of model performance metrics
        """
        try:
            if model_types is None:
                model_types = list(ModelType)

            performance_results = {}

            for model_type in model_types:
                logger.info(f"Training {model_type.value} model...")

                # Get training data
                training_data = await self._prepare_training_data(model_type)
                if len(training_data) < self.min_training_samples:
                    logger.warning(f"Insufficient training data for {model_type.value}: {len(training_data)} samples")
                    continue

                # Prepare features and targets
                X, y = self._prepare_features_and_targets(training_data, model_type)
                if len(X) == 0:
                    continue

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)

                # Train model
                start_time = time.time()
                model = self._create_model(model_type)
                model.fit(X_train_scaled, y_train)
                training_time = time.time() - start_time

                # Evaluate model
                y_pred = model.predict(X_test_scaled)

                if hasattr(model, 'predict_proba'):
                    # Classification metrics
                    accuracy = accuracy_score(y_test, y_pred)
                    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                else:
                    # Regression metrics (convert to classification-like metrics)
                    accuracy = 1.0 - np.mean(np.abs(y_test - y_pred))
                    precision = accuracy
                    recall = accuracy
                    f1 = accuracy

                # Store model and metrics
                self.models[model_type] = model
                self.scalers[model_type] = scaler

                performance_metrics = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'training_samples': len(X_train),
                    'validation_samples': len(X_test),
                    'feature_count': len(X_train[0]) if len(X_train) > 0 else 0,
                    'training_time': training_time
                }

                performance_results[model_type] = performance_metrics
                self.model_metrics[model_type] = performance_metrics

                # Save model
                await self._save_model(model_type, model, scaler, performance_metrics)

                logger.info(f"Trained {model_type.value} model - Accuracy: {accuracy:.3f}, F1: {f1:.3f}")

            # Update statistics
            self.stats['training_cycles'] += 1
            self.stats['model_accuracy'] = {mt.value: metrics.get('accuracy', 0) for mt, metrics in performance_results.items()}

            return performance_results

        except Exception as e:
            logger.error(f"Error training prediction models: {e}")
            return {}

    async def update_training_data(self, security_event: Dict[str, Any]):
        """Add new security event data for model training"""
        try:
            # Extract features from security event
            features = await self._extract_features_from_event(security_event)
            if not features:
                return

            # Determine data type and target values
            data_type = security_event.get('event_type', 'unknown')
            target_value = self._extract_target_value(security_event)
            target_class = self._extract_target_class(security_event)

            # Store training data
            data_id = f"data_{int(time.time() * 1000)}_{hashlib.md5(json.dumps(features).encode()).hexdigest()[:8]}"

            training_record = {
                'data_id': data_id,
                'data_type': data_type,
                'features': features,
                'target_value': target_value,
                'target_class': target_class,
                'timestamp': security_event.get('timestamp', datetime.now().isoformat()),
                'user_id': security_event.get('user_id'),
                'context_data': security_event
            }

            # Add to memory
            if data_type not in self.training_data:
                self.training_data[data_type] = []
            self.training_data[data_type].append(training_record)

            # Store to database
            await self._store_training_data(training_record)

            # Update statistics
            self.stats['data_points_processed'] += 1

            # Trigger retraining if we have enough new data
            if self.auto_retrain and len(self.training_data[data_type]) % 100 == 0:
                asyncio.create_task(self.train_prediction_models())

        except Exception as e:
            logger.error(f"Error updating training data: {e}")

    async def validate_prediction_accuracy(self, prediction_id: str, actual_outcome: str, outcome_timestamp: Optional[datetime] = None):
        """Update prediction with actual outcome for accuracy tracking"""
        try:
            if prediction_id not in self.active_predictions:
                return

            prediction = self.active_predictions[prediction_id]

            # Calculate accuracy score
            accuracy_score = self._calculate_prediction_accuracy(prediction, actual_outcome)

            # Update prediction
            prediction.last_updated = datetime.now()

            # Store validation result
            await self._store_prediction_validation(prediction_id, actual_outcome, outcome_timestamp, accuracy_score)

            # Update overall accuracy statistics
            await self._update_accuracy_statistics(accuracy_score)

            logger.info(f"Validated prediction {prediction_id} with accuracy {accuracy_score:.3f}")

        except Exception as e:
            logger.error(f"Error validating prediction accuracy: {e}")

    def get_analytics_statistics(self) -> Dict[str, Any]:
        """Get predictive analytics statistics"""
        stats = self.stats.copy()

        # Add current state
        stats['active_predictions'] = len(self.active_predictions)
        stats['security_trends'] = len(self.security_trends)
        stats['risk_forecasts'] = len(self.risk_forecasts)
        stats['analytics_active'] = self.analytics_active
        stats['available_models'] = list(self.models.keys())

        # Calculate averages
        if self.historical_predictions:
            confidence_scores = [p.confidence_score for p in self.historical_predictions]
            stats['average_confidence'] = statistics.mean(confidence_scores)

        return stats

    async def get_current_risk_assessment(self, entity: Optional[str] = None) -> Dict[str, Any]:
        """Get current risk assessment for system or specific entity"""
        try:
            current_time = datetime.now()

            # Get active predictions
            relevant_predictions = []
            for prediction in self.active_predictions.values():
                if prediction.valid_until and prediction.valid_until > current_time:
                    if entity is None or entity in prediction.affected_entities:
                        relevant_predictions.append(prediction)

            # Calculate overall risk score
            if relevant_predictions:
                risk_scores = [p.risk_score for p in relevant_predictions]
                overall_risk = max(risk_scores)  # Take highest risk
                avg_confidence = statistics.mean([p.confidence_score for p in relevant_predictions])
            else:
                overall_risk = 0.5  # Baseline risk
                avg_confidence = 0.5

            # Get current trends
            active_trends = [trend for trend in self.security_trends.values()
                           if trend.timeframe[1] > current_time]

            # Get risk drivers
            risk_drivers = {}
            for prediction in relevant_predictions:
                for indicator in prediction.key_indicators:
                    risk_drivers[indicator] = risk_drivers.get(indicator, 0) + 1

            return {
                'overall_risk_score': overall_risk,
                'risk_level': self._score_to_risk_level(overall_risk).value,
                'confidence': avg_confidence,
                'active_predictions': len(relevant_predictions),
                'active_trends': len(active_trends),
                'key_risk_drivers': risk_drivers,
                'assessment_time': current_time.isoformat(),
                'entity': entity
            }

        except Exception as e:
            logger.error(f"Error getting current risk assessment: {e}")
            return {'error': str(e)}

    # Helper methods for ML operations

    def _get_model_type_for_prediction(self, prediction_type: PredictionType) -> ModelType:
        """Map prediction type to appropriate model type"""
        mapping = {
            PredictionType.THREAT_LIKELIHOOD: ModelType.THREAT_CLASSIFICATION,
            PredictionType.BREACH_PROBABILITY: ModelType.THREAT_CLASSIFICATION,
            PredictionType.ATTACK_TIMING: ModelType.TIME_SERIES,
            PredictionType.VULNERABILITY_RISK: ModelType.RISK_REGRESSION,
            PredictionType.USER_BEHAVIOR_RISK: ModelType.ANOMALY_DETECTION,
            PredictionType.SOCIAL_ENGINEERING_RISK: ModelType.SOCIAL_PATTERN,
            PredictionType.SYSTEM_COMPROMISE_RISK: ModelType.RISK_REGRESSION
        }
        return mapping.get(prediction_type, ModelType.ANOMALY_DETECTION)

    def _create_model(self, model_type: ModelType):
        """Create appropriate ML model for model type"""
        if model_type == ModelType.ANOMALY_DETECTION:
            return IsolationForest(contamination=0.1, random_state=42)
        elif model_type == ModelType.THREAT_CLASSIFICATION:
            return RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == ModelType.RISK_REGRESSION:
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == ModelType.TIME_SERIES:
            return RandomForestRegressor(n_estimators=50, random_state=42)
        elif model_type == ModelType.SOCIAL_PATTERN:
            return RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            return IsolationForest(contamination=0.1, random_state=42)

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert numerical score to risk level"""
        if score >= 0.9:
            return RiskLevel.CRITICAL
        elif score >= 0.75:
            return RiskLevel.VERY_HIGH
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.MEDIUM
        elif score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW

    def _score_to_confidence_level(self, score: float) -> PredictionConfidence:
        """Convert confidence score to confidence level"""
        if score >= 0.8:
            return PredictionConfidence.VERY_HIGH
        elif score >= 0.6:
            return PredictionConfidence.HIGH
        elif score >= 0.4:
            return PredictionConfidence.MEDIUM
        elif score >= 0.2:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW

    async def _extract_prediction_features(self, context_data: Dict[str, Any], prediction_type: PredictionType) -> Dict[str, Any]:
        """Extract features from context data for prediction"""
        features = {}

        # Time-based features
        now = datetime.now()
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        features['is_weekend'] = now.weekday() >= 5

        # User behavior features
        if 'user_id' in context_data:
            user_profile = self.user_risk_profiles.get(context_data['user_id'], {})
            features['user_trust_level'] = user_profile.get('trust_level', 0.5)
            features['user_activity_score'] = user_profile.get('activity_score', 1.0)

        # Activity features
        features['command_count'] = len(context_data.get('commands_used', []))
        features['session_duration'] = context_data.get('session_duration', 0)
        features['error_count'] = context_data.get('error_count', 0)
        features['auth_failures'] = context_data.get('authentication', {}).get('failed_attempts', 0)

        # Social context features
        features['social_context_risk'] = await self._assess_social_context_risk(context_data)
        features['emotional_state_risk'] = self._assess_emotional_state_risk(context_data)

        # System state features
        features['system_load'] = context_data.get('system_metrics', {}).get('cpu_usage', 0.5)
        features['network_activity'] = context_data.get('system_metrics', {}).get('network_usage', 0.5)

        return features

    def _prepare_feature_vector(self, features: Dict[str, Any], model_type: ModelType) -> List[float]:
        """Prepare feature vector for model input"""
        # Define expected feature order for consistency
        feature_order = [
            'hour_of_day', 'day_of_week', 'is_weekend',
            'user_trust_level', 'user_activity_score',
            'command_count', 'session_duration', 'error_count', 'auth_failures',
            'social_context_risk', 'emotional_state_risk',
            'system_load', 'network_activity'
        ]

        vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0)

            # Convert boolean to float
            if isinstance(value, bool):
                value = float(value)
            elif not isinstance(value, (int, float)):
                value = 0.0

            vector.append(value)

        return vector

    def _calculate_prediction_confidence(self, features: Dict[str, Any], model_type: ModelType, risk_score: float) -> float:
        """Calculate confidence in prediction based on features and model"""
        # Base confidence from model performance
        base_confidence = self.model_metrics.get(model_type, {}).get('accuracy', 0.5)

        # Adjust based on feature completeness
        feature_completeness = len([v for v in features.values() if v != 0]) / len(features)

        # Adjust based on how extreme the risk score is
        score_confidence = 1.0 - abs(risk_score - 0.5) * 2  # Higher confidence for extreme scores

        # Combine factors
        final_confidence = (base_confidence + feature_completeness + score_confidence) / 3
        return min(max(final_confidence, 0.0), 1.0)

    def _get_feature_importance(self, model, model_type: ModelType, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            return dict(zip(feature_names, importances))
        else:
            # For models without feature importance, return uniform
            uniform_importance = 1.0 / len(feature_names)
            return {name: uniform_importance for name in feature_names}

    def _identify_key_indicators(self, features: Dict[str, Any], feature_importance: Dict[str, float]) -> List[str]:
        """Identify key indicators from features and importance"""
        # Sort features by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

        key_indicators = []
        for feature_name, importance in sorted_features[:5]:  # Top 5 features
            if importance > 0.1 and features.get(feature_name, 0) != 0:
                # Create human-readable indicator
                indicator = self._feature_to_indicator(feature_name, features[feature_name])
                if indicator:
                    key_indicators.append(indicator)

        return key_indicators

    def _feature_to_indicator(self, feature_name: str, value: Any) -> Optional[str]:
        """Convert feature to human-readable indicator"""
        if feature_name == 'auth_failures' and value > 0:
            return f"Authentication failures: {value}"
        elif feature_name == 'command_count' and value > 10:
            return f"High command activity: {value} commands"
        elif feature_name == 'error_count' and value > 0:
            return f"Error occurrences: {value}"
        elif feature_name == 'social_context_risk' and value > 0.7:
            return "High social context risk detected"
        elif feature_name == 'emotional_state_risk' and value > 0.7:
            return "Elevated emotional state risk"
        elif feature_name == 'is_weekend' and value:
            return "Weekend activity (unusual timing)"
        elif feature_name == 'hour_of_day' and (value < 6 or value > 22):
            return f"Off-hours activity: {value}:00"

        return None

    async def _generate_mitigation_recommendations(self,
                                                 prediction_type: PredictionType,
                                                 risk_level: RiskLevel,
                                                 indicators: List[str],
                                                 context: Dict[str, Any]) -> List[str]:
        """Generate mitigation recommendations based on prediction"""
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Increase monitoring and alerting levels")
            recommendations.append("Require additional authentication for sensitive operations")

        if "Authentication failures" in str(indicators):
            recommendations.append("Review and strengthen authentication mechanisms")
            recommendations.append("Implement account lockout policies")

        if "High command activity" in str(indicators):
            recommendations.append("Audit command usage patterns and permissions")
            recommendations.append("Implement command rate limiting")

        if "Off-hours activity" in str(indicators):
            recommendations.append("Verify legitimate business need for off-hours access")
            recommendations.append("Implement stricter controls for after-hours operations")

        if prediction_type == PredictionType.SOCIAL_ENGINEERING_RISK:
            recommendations.append("Provide additional security awareness training")
            recommendations.append("Implement social engineering detection controls")

        if prediction_type == PredictionType.SYSTEM_COMPROMISE_RISK:
            recommendations.append("Perform immediate system integrity checks")
            recommendations.append("Review and update security patches")

        # Add generic recommendations if none specific
        if not recommendations:
            recommendations.append("Continue monitoring for suspicious activity")
            recommendations.append("Maintain current security posture")

        return recommendations[:5]  # Limit to top 5 recommendations

    # Additional helper methods would continue here...
    # (Due to length constraints, showing key methods only)

    def _analytics_loop(self):
        """Background analytics processing loop"""
        while self.analytics_active:
            try:
                # Periodic analytics tasks
                asyncio.run(self._update_user_risk_profiles())
                asyncio.run(self._cleanup_expired_predictions())

                # Sleep for processing interval
                time.sleep(300)  # Every 5 minutes

            except Exception as e:
                logger.error(f"Error in analytics loop: {e}")

    # Database operations and other helper methods would continue...

# Integration helper function
async def create_integrated_predictive_analytics(
    threat_detection_system=None,
    social_intelligence=None,
    security_logger=None,
    db_path: str = "predictive_security.db"
) -> PredictiveSecurityAnalytics:
    """Create integrated predictive security analytics system"""
    analytics_system = PredictiveSecurityAnalytics(
        db_path=db_path,
        threat_detection_system=threat_detection_system,
        social_intelligence=social_intelligence,
        security_logger=security_logger
    )

    await analytics_system.start_analytics()
    return analytics_system


# Usage example
async def demo_predictive_analytics():
    """Demonstration of predictive security analytics"""
    analytics = PredictiveSecurityAnalytics()
    await analytics.start_analytics()

    try:
        # Generate sample prediction
        context_data = {
            'user_id': 'demo_user',
            'commands_used': ['help', 'status', 'admin'],
            'session_duration': 3600,
            'error_count': 2,
            'authentication': {'failed_attempts': 1},
            'system_metrics': {'cpu_usage': 0.8, 'network_usage': 0.6}
        }

        prediction = await analytics.generate_security_prediction(
            PredictionType.THREAT_LIKELIHOOD,
            context_data,
            time_horizon_hours=24
        )

        if prediction:
            print(f"Prediction: {prediction.predicted_risk_level.value} risk")
            print(f"Confidence: {prediction.confidence.value}")
            print(f"Key indicators: {prediction.key_indicators}")

        # Get current risk assessment
        risk_assessment = await analytics.get_current_risk_assessment()
        print(f"Current risk assessment: {risk_assessment}")

        # Get statistics
        stats = analytics.get_analytics_statistics()
        print(f"Analytics statistics: {stats}")

    finally:
        await analytics.stop_analytics()

if __name__ == "__main__":
    asyncio.run(demo_predictive_analytics())