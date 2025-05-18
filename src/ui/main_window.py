from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QGroupBox, QFormLayout, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from typing import Dict, Any

class MainWindow(QMainWindow):
    def __init__(self, market_impact_model, slippage_model, maker_taker_model, ws_client):
        super().__init__()
        self.market_impact_model = market_impact_model
        self.slippage_model = slippage_model
        self.maker_taker_model = maker_taker_model
        self.ws_client = ws_client
        
        self.setWindowTitle("GoQuant Trade Simulator")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create input panel
        input_panel = self._create_input_panel()
        main_layout.addWidget(input_panel)
        
        # Create output panel
        output_panel = self._create_output_panel()
        main_layout.addWidget(output_panel)
        
        # Register WebSocket callback
        self.ws_client.register_callback(self._on_orderbook_update)
        
    def _create_input_panel(self) -> QGroupBox:
        """Create the input parameters panel."""
        panel = QGroupBox("Input Parameters")
        layout = QFormLayout()
        
        # Exchange selection
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItem("OKX")
        layout.addRow("Exchange:", self.exchange_combo)
        
        # Asset selection
        self.asset_combo = QComboBox()
        self.asset_combo.addItem("BTC-USDT-SWAP")
        layout.addRow("Asset:", self.asset_combo)
        
        # Order type
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItem("Market")
        layout.addRow("Order Type:", self.order_type_combo)
        
        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 1000000)
        self.quantity_spin.setValue(100)
        self.quantity_spin.setSuffix(" USD")
        layout.addRow("Quantity:", self.quantity_spin)
        
        # Volatility
        self.volatility_spin = QDoubleSpinBox()
        self.volatility_spin.setRange(0, 100)
        self.volatility_spin.setValue(1.0)
        self.volatility_spin.setSuffix("%")
        layout.addRow("Volatility:", self.volatility_spin)
        
        # Fee tier
        self.fee_tier_combo = QComboBox()
        self.fee_tier_combo.addItems(["Tier 1", "Tier 2", "Tier 3"])
        layout.addRow("Fee Tier:", self.fee_tier_combo)
        
        panel.setLayout(layout)
        return panel
        
    def _create_output_panel(self) -> QGroupBox:
        """Create the output parameters panel."""
        panel = QGroupBox("Output Parameters")
        layout = QFormLayout()
        
        # Expected Slippage
        self.slippage_label = QLabel("0.00%")
        layout.addRow("Expected Slippage:", self.slippage_label)
        
        # Expected Fees
        self.fees_label = QLabel("0.00 USD")
        layout.addRow("Expected Fees:", self.fees_label)
        
        # Market Impact
        self.market_impact_label = QLabel("0.00%")
        layout.addRow("Market Impact:", self.market_impact_label)
        
        # Net Cost
        self.net_cost_label = QLabel("0.00 USD")
        layout.addRow("Net Cost:", self.net_cost_label)
        
        # Maker/Taker Proportion
        self.maker_taker_label = QLabel("0.00% / 0.00%")
        layout.addRow("Maker/Taker:", self.maker_taker_label)
        
        # Internal Latency
        self.latency_label = QLabel("0.00 ms")
        layout.addRow("Internal Latency:", self.latency_label)
        
        panel.setLayout(layout)
        return panel
        
    @pyqtSlot(dict)
    async def _on_orderbook_update(self, data: Dict[str, Any]):
        """Handle new orderbook updates."""
        try:
            # Get current input parameters
            quantity = self.quantity_spin.value()
            volatility = self.volatility_spin.value() / 100
            
            # Calculate expected slippage
            slippage = self.slippage_model.calculate(data, quantity)
            self.slippage_label.setText(f"{slippage:.2f}%")
            
            # Calculate fees
            fees = self._calculate_fees(quantity)
            self.fees_label.setText(f"{fees:.2f} USD")
            
            # Calculate market impact
            impact = self.market_impact_model.calculate(data, quantity, volatility)
            self.market_impact_label.setText(f"{impact:.2f}%")
            
            # Calculate net cost
            net_cost = (slippage + impact) * quantity / 100 + fees
            self.net_cost_label.setText(f"{net_cost:.2f} USD")
            
            # Calculate maker/taker proportion
            maker_taker = self.maker_taker_model.calculate(data, quantity)
            self.maker_taker_label.setText(f"{maker_taker['maker']:.2f}% / {maker_taker['taker']:.2f}%")
            
            # Update latency
            self.latency_label.setText(f"{data.get('processing_time', 0):.2f} ms")
            
        except Exception as e:
            print(f"Error updating UI: {str(e)}")
            
    def _calculate_fees(self, quantity: float) -> float:
        """Calculate trading fees based on quantity and fee tier."""
        # OKX fee tiers (example values)
        fee_tiers = {
            "Tier 1": 0.001,  # 0.1%
            "Tier 2": 0.0008,  # 0.08%
            "Tier 3": 0.0006,  # 0.06%
        }
        
        tier = self.fee_tier_combo.currentText()
        return quantity * fee_tiers[tier] 