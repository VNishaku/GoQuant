import numpy as np
from typing import Dict, Any
import logging
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

class MakerTakerModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = LogisticRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def calculate(self, orderbook: Dict[str, Any], quantity: float) -> Dict[str, float]:
        """
        Calculate the probability of order execution as maker vs taker.
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in USD
            
        Returns:
            Dict[str, float]: Dictionary containing maker and taker probabilities
        """
        try:
            # Extract features
            features = self._extract_features(orderbook, quantity)
            
            # If model is not trained, use a simple heuristic
            if not self.is_trained:
                return self._calculate_heuristic_proportions(orderbook, quantity)
                
            # Scale features
            scaled_features = self.scaler.transform([features])
            
            # Predict probabilities
            probabilities = self.model.predict_proba(scaled_features)[0]
            
            return {
                "maker": probabilities[0] * 100,
                "taker": probabilities[1] * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating maker/taker proportions: {str(e)}")
            return {"maker": 50.0, "taker": 50.0}
            
    def _extract_features(self, orderbook: Dict[str, Any], quantity: float) -> np.ndarray:
        """Extract features for maker/taker prediction."""
        asks = np.array(orderbook["asks"])
        bids = np.array(orderbook["bids"])
        
        # Calculate basic orderbook metrics
        mid_price = (asks[0][0] + bids[0][0]) / 2
        spread = asks[0][0] - bids[0][0]
        spread_percentage = (spread / mid_price) * 100
        
        # Calculate depth metrics
        ask_depth = np.sum(asks[:, 1] * asks[:, 0])
        bid_depth = np.sum(bids[:, 1] * bids[:, 0])
        total_depth = ask_depth + bid_depth
        
        # Calculate imbalance
        depth_imbalance = (ask_depth - bid_depth) / total_depth
        
        # Calculate price levels
        price_levels = len(asks)
        
        # Calculate quantity relative to depth
        quantity_ratio = quantity / total_depth
        
        # Calculate orderbook pressure
        pressure = (ask_depth - bid_depth) / (ask_depth + bid_depth)
        
        return np.array([
            spread_percentage,
            depth_imbalance,
            price_levels,
            quantity_ratio,
            pressure,
            np.log10(quantity)  # Log scale for quantity
        ])
        
    def _calculate_heuristic_proportions(self, orderbook: Dict[str, Any], quantity: float) -> Dict[str, float]:
        """Calculate maker/taker proportions using a simple heuristic when model is not trained."""
        asks = np.array(orderbook["asks"])
        bids = np.array(orderbook["bids"])
        
        # Calculate spread
        spread = asks[0][0] - bids[0][0]
        mid_price = (asks[0][0] + bids[0][0]) / 2
        spread_percentage = (spread / mid_price) * 100
        
        # Calculate depth
        ask_depth = np.sum(asks[:, 1] * asks[:, 0])
        bid_depth = np.sum(bids[:, 1] * bids[:, 0])
        total_depth = ask_depth + bid_depth
        
        # Calculate quantity impact
        quantity_ratio = quantity / total_depth
        
        # Calculate maker probability
        # Higher spread and lower quantity ratio favor maker orders
        maker_prob = 50.0 + (spread_percentage * 2) - (quantity_ratio * 100)
        
        # Ensure probabilities are between 0 and 100
        maker_prob = max(0.0, min(100.0, maker_prob))
        taker_prob = 100.0 - maker_prob
        
        return {
            "maker": maker_prob,
            "taker": taker_prob
        }
        
    def train(self, historical_data: list):
        """
        Train the maker/taker model using historical data.
        
        Args:
            historical_data: List of dictionaries containing historical orderbook states
                           and actual execution types (0 for maker, 1 for taker)
        """
        try:
            if not historical_data:
                return
                
            # Extract features and targets
            X = []
            y = []
            
            for data in historical_data:
                features = self._extract_features(data["orderbook"], data["quantity"])
                X.append(features)
                y.append(data["execution_type"])
                
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
        except Exception as e:
            self.logger.error(f"Error training maker/taker model: {str(e)}")
            self.is_trained = False 