import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.websocket.client import WebSocketClient
from src.models.market_impact import MarketImpactModel
from src.models.slippage import SlippageModel
from src.models.maker_taker import MakerTakerModel

async def main():
    # Initialize Qt Application
    app = QApplication(sys.argv)
    
    # Initialize models
    market_impact_model = MarketImpactModel()
    slippage_model = SlippageModel()
    maker_taker_model = MakerTakerModel()
    
    # Initialize WebSocket client
    ws_client = WebSocketClient(
        url="wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"
    )
    
    # Initialize main window
    window = MainWindow(
        market_impact_model=market_impact_model,
        slippage_model=slippage_model,
        maker_taker_model=maker_taker_model,
        ws_client=ws_client
    )
    
    # Start WebSocket connection
    await ws_client.connect()
    
    # Show main window
    window.show()
    
    # Start event loop
    return app.exec()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print(f"Application error: {str(e)}")
        sys.exit(1) 