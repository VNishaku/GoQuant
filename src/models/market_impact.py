import numpy as np
from typing import Dict, Any
import logging

class MarketImpactModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate(self, orderbook: Dict[str, Any], quantity: float, volatility: float) -> float:
        """
        Calculate market impact using the Almgren-Chriss model.
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in USD
            volatility: Market volatility (0-1)
            
        Returns:
            float: Estimated market impact as a percentage
        """
        try:
            # Extract orderbook data
            asks = np.array(orderbook["asks"])
            bids = np.array(orderbook["bids"])
            
            # Calculate mid price
            mid_price = (asks[0][0] + bids[0][0]) / 2
            
            # Calculate temporary impact parameters
            eta = self._calculate_temporary_impact(asks, bids, quantity)
            
            # Calculate permanent impact parameters
            gamma = self._calculate_permanent_impact(asks, bids, quantity)
            
            # Calculate risk aversion parameter (lambda)
            # Higher volatility leads to higher risk aversion
            lambda_param = 0.1 * (1 + volatility)
            
            # Calculate optimal execution time (T)
            # This is a simplified version - in practice, this would be more complex
            T = self._calculate_optimal_time(quantity, volatility)
            
            # Calculate market impact using Almgren-Chriss formula
            # MI = η * (Q/T) + γ * Q + λ * σ * sqrt(T)
            # where:
            # η = temporary impact parameter
            # γ = permanent impact parameter
            # λ = risk aversion parameter
            # σ = volatility
            # T = execution time
            # Q = order quantity
            
            temporary_impact = eta * (quantity / T)
            permanent_impact = gamma * quantity
            risk_term = lambda_param * volatility * np.sqrt(T)
            
            total_impact = temporary_impact + permanent_impact + risk_term
            
            # Convert to percentage
            impact_percentage = (total_impact / quantity) * 100
            
            return impact_percentage
            
        except Exception as e:
            self.logger.error(f"Error calculating market impact: {str(e)}")
            return 0.0
            
    def _calculate_temporary_impact(self, asks: np.ndarray, bids: np.ndarray, quantity: float) -> float:
        """Calculate temporary market impact parameter."""
        # Calculate average spread
        spread = np.mean(asks[:, 0] - bids[:, 0])
        
        # Calculate average depth
        avg_depth = np.mean(np.concatenate([asks[:, 1], bids[:, 1]]))
        
        # Temporary impact increases with spread and decreases with depth
        return 0.1 * (spread / avg_depth)
        
    def _calculate_permanent_impact(self, asks: np.ndarray, bids: np.ndarray, quantity: float) -> float:
        """Calculate permanent market impact parameter."""
        # Calculate price levels
        price_levels = len(asks)
        
        # Permanent impact decreases with more price levels
        return 0.05 / np.sqrt(price_levels)
        
    def _calculate_optimal_time(self, quantity: float, volatility: float) -> float:
        """Calculate optimal execution time."""
        # Base time in seconds
        base_time = 300  # 5 minutes
        
        # Adjust time based on quantity and volatility
        # Larger orders and higher volatility lead to longer execution times
        quantity_factor = np.log10(quantity) / 3  # Normalize quantity impact
        volatility_factor = volatility * 2
        
        return base_time * (1 + quantity_factor + volatility_factor) 