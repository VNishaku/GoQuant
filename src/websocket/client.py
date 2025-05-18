import json
import asyncio
import websockets
import logging
from typing import Callable, Dict, List, Optional
from datetime import datetime

class WebSocketClient:
    def __init__(self, url: str):
        self.url = url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.callbacks: List[Callable] = []
        self.running = False
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Establish WebSocket connection and start message processing."""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            asyncio.create_task(self._process_messages())
            self.logger.info(f"Connected to WebSocket at {self.url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket: {str(e)}")
            raise
            
    async def _process_messages(self):
        """Process incoming WebSocket messages."""
        while self.running:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Process and validate the orderbook data
                processed_data = self._process_orderbook(data)
                
                # Notify all registered callbacks
                for callback in self.callbacks:
                    await callback(processed_data)
                    
            except websockets.ConnectionClosed:
                self.logger.warning("WebSocket connection closed")
                await self._reconnect()
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                
    def _process_orderbook(self, data: Dict) -> Dict:
        """Process and validate orderbook data."""
        try:
            # Validate required fields
            required_fields = ["timestamp", "exchange", "symbol", "asks", "bids"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
                    
            # Convert string timestamps to datetime objects
            data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            
            # Convert price and quantity strings to floats
            data["asks"] = [[float(price), float(qty)] for price, qty in data["asks"]]
            data["bids"] = [[float(price), float(qty)] for price, qty in data["bids"]]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error processing orderbook data: {str(e)}")
            raise
            
    async def _reconnect(self):
        """Attempt to reconnect to the WebSocket server."""
        retry_delay = 1
        max_retry_delay = 30
        
        while self.running:
            try:
                self.logger.info(f"Attempting to reconnect in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                self.websocket = await websockets.connect(self.url)
                self.logger.info("Successfully reconnected")
                return
            except Exception as e:
                self.logger.error(f"Reconnection failed: {str(e)}")
                retry_delay = min(retry_delay * 2, max_retry_delay)
                
    def register_callback(self, callback: Callable):
        """Register a callback function to be called with each new orderbook update."""
        self.callbacks.append(callback)
        
    async def close(self):
        """Close the WebSocket connection."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket connection closed") 