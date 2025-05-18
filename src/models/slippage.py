import numpy as np
from typing import Dict, Any
import logging
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

class SlippageModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def calculate(self, orderbook: Dict[str, Any], quantity: float) -> float:
        """
        Calculate expected slippage using a linear regression model.
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in USD
            
        Returns:
            float: Expected slippage as a percentage
        """
        try:
            # Extract features
            features = self._extract_features(orderbook, quantity)
            
            # If model is not trained, use a simple heuristic
            if not self.is_trained:
                return self._calculate_heuristic_slippage(orderbook, quantity)
                
            # Scale features
            scaled_features = self.scaler.transform([features])
            
            # Predict slippage
            slippage = self.model.predict(scaled_features)[0]
            
            # Ensure non-negative slippage
            return max(0.0, slippage)
            
        except Exception as e:
            self.logger.error(f"Error calculating slippage: {str(e)}")
            return 0.0
            
    def _extract_features(self, orderbook: Dict[str, Any], quantity: float) -> np.ndarray:
        """Extract features for slippage prediction."""
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
        depth_imbalance = abs(ask_depth - bid_depth) / total_depth
        
        # Calculate price levels
        price_levels = len(asks)
        
        # Calculate quantity relative to depth
        quantity_ratio = quantity / total_depth
        
        return np.array([
            spread_percentage,
            depth_imbalance,
            price_levels,
            quantity_ratio,
            np.log10(quantity)  # Log scale for quantity
        ])
        
    def _calculate_heuristic_slippage(self, orderbook: Dict[str, Any], quantity: float) -> float:
        """Calculate slippage using a simple heuristic when model is not trained."""
        asks = np.array(orderbook["asks"])
        bids = np.array(orderbook["bids"])
        
        # Calculate mid price
        mid_price = (asks[0][0] + bids[0][0]) / 2
        
        # Calculate spread
        spread = asks[0][0] - bids[0][0]
        spread_percentage = (spread / mid_price) * 100
        
        # Calculate depth
        total_depth = np.sum(asks[:, 1] * asks[:, 0]) + np.sum(bids[:, 1] * bids[:, 0])
        
        # Calculate quantity impact
        quantity_impact = (quantity / total_depth) * 100
        
        # Combine factors
        slippage = spread_percentage * 0.5 + quantity_impact * 0.5
        
        return slippage
        
    def train(self, historical_data: list):
        """
        Train the slippage model using historical data.
        
        Args:
            historical_data: List of dictionaries containing historical orderbook states
                           and actual slippage values
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
                y.append(data["actual_slippage"])
                
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
        except Exception as e:
            self.logger.error(f"Error training slippage model: {str(e)}")
            self.is_trained = False 