"""
Hebbian Dimension Associator
Learns which personality dimensions naturally co-activate together
through Hebbian learning

Example: When empathy is high, brevity often co-activates (stressed users
want empathetic but brief responses). This component learns these patterns.
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import logging

from .hebbian_types import (
    DimensionCoactivation,
    MultiDimensionalPattern,
    NegativeCorrelation,
    DimensionPrediction,
    PERSONALITY_DIMENSIONS,
    DEFAULT_LEARNING_RATE,
    DEFAULT_ACTIVATION_THRESHOLD,
    DEFAULT_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


class HebbianDimensionAssociator:
    """
    Learns personality dimension co-activations through Hebbian learning

    Core Algorithm:
    1. Observe which dimensions are active simultaneously
    2. Strengthen pairwise co-activations via Δw = η * x1 * x2
    3. Detect multi-dimensional patterns (3+ dims)
    4. Predict dimension values based on known activations

    Example:
        >>> associator = HebbianDimensionAssociator()
        >>> # Observe empathy + brevity co-activation
        >>> associator.observe_activations({
        ...     'emotional_support_style': 0.85,
        ...     'response_length_preference': 0.2  # Brief
        ... })
        >>> # Later, predict based on empathy alone
        >>> predictions = associator.predict_coactivations(
        ...     {'emotional_support_style': 0.8}
        ... )
        >>> # Should predict brevity
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        learning_rate: float = DEFAULT_LEARNING_RATE,
        activation_threshold: float = DEFAULT_ACTIVATION_THRESHOLD
    ):
        """
        Initialize dimension associator

        Args:
            db_path: Path to SQLite database
            learning_rate: Rate of co-activation strengthening
            activation_threshold: Threshold for considering dimension "active"
        """
        self.db_path = db_path
        self.learning_rate = learning_rate
        self.activation_threshold = activation_threshold

        # Valid dimensions
        self._dimensions = PERSONALITY_DIMENSIONS.copy()

        # Initialize database
        self._init_db()

        logger.info(f"HebbianDimensionAssociator initialized (lr={learning_rate})")

    def _init_db(self) -> None:
        """Ensure database tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='dimension_coactivations'
            """)
            if not cursor.fetchone():
                logger.warning("dimension_coactivations table not found - schema may need to be applied")

    # ========================================================================
    # CORE LEARNING METHODS
    # ========================================================================

    def observe_activations(
        self,
        dimensions: Dict[str, float],
        session_id: Optional[str] = None
    ) -> int:
        """
        Observe dimension activations, update co-activations

        Algorithm:
        1. Filter to active dimensions (value > threshold OR value < 1-threshold for low values)
        2. For each pair of dimensions:
           - Strengthen co-activation: Δw = η * x1 * x2
        3. Detect multi-dimensional patterns if 3+ active
        4. Check for negative correlations
        5. Update database

        Args:
            dimensions: Dict of dimension_name -> current_value (0.0-1.0)
            session_id: Optional session identifier

        Returns:
            int: Number of co-activations updated
        """
        # Filter to meaningful activations (high or low, not neutral)
        active_dims = {}
        for dim, value in dimensions.items():
            if dim in self._dimensions:
                # Active if significantly high OR significantly low
                if value >= self.activation_threshold or value <= (1.0 - self.activation_threshold):
                    active_dims[dim] = value

        if len(active_dims) < 2:
            return 0  # Need at least 2 dimensions for co-activation

        updates = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # For each pair of active dimensions
            dim_list = list(active_dims.keys())
            for i in range(len(dim_list)):
                for j in range(i + 1, len(dim_list)):
                    dim1, dim2 = self._normalize_dim_pair(dim_list[i], dim_list[j])
                    val1 = active_dims[dim_list[i]]
                    val2 = active_dims[dim_list[j]]

                    # Get current co-activation strength
                    current = self._get_coactivation_from_db(cursor, dim1, dim2)

                    # Hebbian update: Δw = η * x1 * x2
                    # Use absolute deviation from 0.5 to capture both high and low activations
                    activation1 = abs(val1 - 0.5) * 2  # Scale to 0-1
                    activation2 = abs(val2 - 0.5) * 2

                    delta = self.learning_rate * activation1 * activation2
                    new_strength = self._cap_strength(current + delta)

                    # Update or insert
                    cursor.execute("""
                        INSERT INTO dimension_coactivations
                        (dim1, dim2, strength, observation_count, last_updated, first_observed)
                        VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))
                        ON CONFLICT(dim1, dim2) DO UPDATE SET
                            strength = ?,
                            observation_count = observation_count + 1,
                            last_updated = datetime('now')
                    """, (dim1, dim2, new_strength, new_strength))
                    updates += 1

            # Log observation for debugging
            cursor.execute("""
                INSERT INTO coactivation_observations
                (timestamp, dimensions_json, session_id)
                VALUES (datetime('now'), ?, ?)
            """, (json.dumps(dimensions), session_id))

            # Detect multi-dimensional pattern if 3+ dimensions
            if len(active_dims) >= 3:
                self._update_multi_dim_pattern(cursor, active_dims)

            conn.commit()

        logger.debug(f"Updated {updates} co-activations from {len(active_dims)} active dims")
        return updates

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_coactivation_strength(
        self,
        dim1: str,
        dim2: str
    ) -> float:
        """
        Get co-activation strength between two dimensions

        Args:
            dim1: First dimension name
            dim2: Second dimension name

        Returns:
            float: Co-activation strength (0.0-1.0), default 0.0
        """
        dim1, dim2 = self._normalize_dim_pair(dim1, dim2)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            return self._get_coactivation_from_db(cursor, dim1, dim2)

    def get_strongest_coactivations(
        self,
        dimension: str,
        n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get dimensions that most strongly co-activate with given dimension

        Args:
            dimension: Dimension name
            n: Number of top co-activations to return

        Returns:
            List of (other_dimension, strength) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    CASE WHEN dim1 = ? THEN dim2 ELSE dim1 END as other_dim,
                    strength
                FROM dimension_coactivations
                WHERE dim1 = ? OR dim2 = ?
                ORDER BY strength DESC
                LIMIT ?
            """, (dimension, dimension, dimension, n))
            return cursor.fetchall()

    # ========================================================================
    # PREDICTION METHODS
    # ========================================================================

    def predict_coactivations(
        self,
        known_dimensions: Dict[str, float],
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> Dict[str, DimensionPrediction]:
        """
        Predict other dimension values based on known active dimensions

        Algorithm:
        1. For each known dimension that's active (> threshold)
        2. Find strongly co-activated dimensions
        3. Predict their values: predicted_val = known_val * coact_strength
        4. Average predictions if multiple sources
        5. Return high-confidence predictions only

        Args:
            known_dimensions: Dict of known dimension_name -> value
            threshold: Minimum confidence for predictions

        Returns:
            Dict of predicted dimension_name -> DimensionPrediction
        """
        # Filter to active known dimensions
        active_known = {
            dim: val for dim, val in known_dimensions.items()
            if val >= self.activation_threshold or val <= (1.0 - self.activation_threshold)
        }

        if not active_known:
            return {}

        # Collect predictions from each active dimension
        predictions: Dict[str, List[Tuple[float, float, str]]] = defaultdict(list)
        # predictions[dim] = [(predicted_value, confidence, source_dim), ...]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for known_dim, known_val in active_known.items():
                # Get strong co-activations for this dimension
                coacts = self.get_strongest_coactivations(known_dim, n=10)

                for other_dim, strength in coacts:
                    if other_dim not in known_dimensions and strength >= threshold:
                        # Predict value based on co-activation
                        # If known dim is high (>0.5), predict other dim high
                        # If known dim is low (<0.5), predict other dim low
                        # Scale by co-activation strength
                        if known_val > 0.5:
                            predicted_val = 0.5 + (known_val - 0.5) * strength
                        else:
                            predicted_val = 0.5 - (0.5 - known_val) * strength

                        # Confidence based on strength and activation intensity
                        confidence = strength * abs(known_val - 0.5) * 2

                        predictions[other_dim].append((predicted_val, confidence, known_dim))

        # Aggregate predictions
        result = {}
        for dim, preds in predictions.items():
            if not preds:
                continue

            # Weighted average by confidence
            total_conf = sum(p[1] for p in preds)
            if total_conf > 0:
                avg_val = sum(p[0] * p[1] for p in preds) / total_conf
                avg_conf = total_conf / len(preds)
                sources = [p[2] for p in preds]

                if avg_conf >= threshold:
                    result[dim] = DimensionPrediction(
                        dimension=dim,
                        predicted_value=avg_val,
                        confidence=avg_conf,
                        sources=sources
                    )

        return result

    # ========================================================================
    # PATTERN DETECTION METHODS
    # ========================================================================

    def get_multi_dim_patterns(
        self,
        min_frequency: int = 3
    ) -> List[MultiDimensionalPattern]:
        """
        Get recurring patterns of 3+ dimensions activating together

        Args:
            min_frequency: Minimum observation count to include

        Returns:
            List of MultiDimensionalPattern objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern_id, dimensions_json, frequency, avg_satisfaction,
                       last_seen, first_seen
                FROM multi_dim_patterns
                WHERE frequency >= ?
                ORDER BY frequency DESC
            """, (min_frequency,))

            patterns = []
            for row in cursor.fetchall():
                patterns.append(MultiDimensionalPattern(
                    pattern_id=row[0],
                    dimensions=json.loads(row[1]),
                    frequency=row[2],
                    avg_satisfaction=row[3],
                    last_observed=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                    first_observed=datetime.fromisoformat(row[5]) if row[5] else datetime.now()
                ))
            return patterns

    def detect_negative_correlations(
        self,
        min_observations: int = 10
    ) -> List[NegativeCorrelation]:
        """
        Detect dimension pairs that anti-correlate
        (one high when other low)

        Args:
            min_observations: Minimum observations to analyze

        Returns:
            List of NegativeCorrelation objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dim_high, dim_low, correlation_strength, observation_count
                FROM negative_correlations
                WHERE observation_count >= ?
                ORDER BY correlation_strength DESC
            """, (min_observations,))

            return [
                NegativeCorrelation(
                    dim_high=row[0],
                    dim_low=row[1],
                    correlation_strength=row[2],
                    observation_count=row[3]
                )
                for row in cursor.fetchall()
            ]

    def _update_multi_dim_pattern(
        self,
        cursor: sqlite3.Cursor,
        active_dims: Dict[str, float]
    ) -> None:
        """Update or create multi-dimensional pattern"""
        # Create pattern ID from sorted dimension names
        sorted_dims = sorted(active_dims.keys())
        pattern_id = hashlib.md5('|'.join(sorted_dims).encode()).hexdigest()[:16]

        cursor.execute("""
            INSERT INTO multi_dim_patterns
            (pattern_id, dimensions_json, frequency, last_seen, first_seen)
            VALUES (?, ?, 1, datetime('now'), datetime('now'))
            ON CONFLICT(pattern_id) DO UPDATE SET
                frequency = frequency + 1,
                last_seen = datetime('now')
        """, (pattern_id, json.dumps(active_dims)))

    # ========================================================================
    # EXPORT & DEBUG METHODS
    # ========================================================================

    def export_coactivation_matrix(self) -> List[Dict]:
        """
        Export co-activation matrix for analysis

        Returns:
            List of dicts with keys: dim1, dim2, strength, observations
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dim1, dim2, strength, observation_count, last_updated
                FROM dimension_coactivations
                ORDER BY strength DESC
            """)
            return [
                {
                    'dim1': row[0],
                    'dim2': row[1],
                    'strength': row[2],
                    'observations': row[3],
                    'last_updated': row[4]
                }
                for row in cursor.fetchall()
            ]

    def get_statistics(self) -> Dict[str, any]:
        """Get system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total co-activations
            cursor.execute("SELECT COUNT(*) FROM dimension_coactivations")
            total = cursor.fetchone()[0]

            # Strong co-activations
            cursor.execute("""
                SELECT COUNT(*) FROM dimension_coactivations WHERE strength >= ?
            """, (DEFAULT_CONFIDENCE_THRESHOLD,))
            strong = cursor.fetchone()[0]

            # Average strength
            cursor.execute("SELECT AVG(strength) FROM dimension_coactivations")
            avg_strength = cursor.fetchone()[0] or 0.0

            # Multi-dim patterns
            cursor.execute("SELECT COUNT(*) FROM multi_dim_patterns")
            patterns = cursor.fetchone()[0]

            # Most connected dimension
            cursor.execute("""
                SELECT dim1, COUNT(*) as connections
                FROM dimension_coactivations
                GROUP BY dim1
                ORDER BY connections DESC
                LIMIT 1
            """)
            most_connected = cursor.fetchone()

            return {
                'total_coactivations': total,
                'strong_coactivations': strong,
                'average_strength': round(avg_strength, 3),
                'multi_dim_patterns': patterns,
                'most_connected_dim': most_connected[0] if most_connected else None
            }

    def visualize_coactivation_network(
        self,
        output_path: str = "coactivation_network.png",
        min_strength: float = 0.3
    ) -> bool:
        """
        Generate visualization of co-activation network

        Args:
            output_path: Path to save visualization
            min_strength: Minimum strength to show edge

        Returns:
            bool: True if visualization created successfully
        """
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("networkx/matplotlib not available for visualization")
            return False

        # Build graph
        G = nx.Graph()

        # Add all dimensions as nodes
        for dim in self._dimensions:
            G.add_node(dim)

        # Add edges for strong co-activations
        matrix = self.export_coactivation_matrix()
        for row in matrix:
            if row['strength'] >= min_strength:
                G.add_edge(row['dim1'], row['dim2'], weight=row['strength'])

        # Draw
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, k=2)

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000)
        nx.draw_networkx_labels(G, pos, font_size=8)

        # Draw edges with width based on strength
        edges = G.edges(data=True)
        widths = [e[2].get('weight', 0.1) * 5 for e in edges]
        nx.draw_networkx_edges(G, pos, width=widths, alpha=0.6)

        plt.title("Personality Dimension Co-activation Network")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

        logger.info(f"Saved co-activation visualization to {output_path}")
        return True

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _normalize_dim_pair(
        self,
        dim1: str,
        dim2: str
    ) -> Tuple[str, str]:
        """Ensure dim1 < dim2 to avoid duplicates"""
        if dim1 > dim2:
            return dim2, dim1
        return dim1, dim2

    def _cap_strength(self, strength: float) -> float:
        """Cap strength to valid range [0.0, 1.0]"""
        return max(0.0, min(1.0, strength))

    def _get_coactivation_from_db(
        self,
        cursor: sqlite3.Cursor,
        dim1: str,
        dim2: str
    ) -> float:
        """Get co-activation strength from database, default 0.0"""
        cursor.execute("""
            SELECT strength FROM dimension_coactivations
            WHERE dim1 = ? AND dim2 = ?
        """, (dim1, dim2))
        result = cursor.fetchone()
        return result[0] if result else 0.0
