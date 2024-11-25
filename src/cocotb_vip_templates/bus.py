import cocotb
from cocotb_bus.bus import Bus as BusBaseClass

class Bus(BusBaseClass):  
    """Bus class for ocx_dlx_top module."""

    def __init__(
        self,
        dut: cocotb.handle, 
        prefix: str = "",
        suffix: str = "",
        bus_seperator: str = "_",
        clk: str = "clk_156_25MHz",  
        reset: str = "hb_gtwiz_reset_all_in", 
        active_high_reset: bool = True, 
        uppercase: bool = False,
    ):
        """Constructor for the DLX bus.

        Args:
            dut (cocotb.handle): Handle to the DUT (ocx_dlx_top)
            prefix (str): Prefix for signal names (if any)
            suffix (str): Suffix for signal names (if any)
            bus_seperator (str): Separator for bus signal names (e.g., '_')
            clk (str): Name of the clock signal
            reset (str): Name of the reset signal
            active_high_reset (bool): True if reset is active high
            uppercase (bool): True if signal names are uppercase in the DUT
        """

        self.dut = dut

        # Create a list to store all signal names
        all_signals = [
            # --- TLX to DLX interface ---
            "tlx_dlx_flit_valid", "tlx_dlx_flit", "tlx_dlx_debug_encode", "tlx_dlx_debug_info",

            # --- DLX to TLX interface ---
            "dlx_tlx_flit_valid", "dlx_tlx_flit", "dlx_tlx_flit_crc_err", 
            "dlx_tlx_link_up", "dlx_config_info", "ro_dlx_version", "dlx_tlx_init_flit_depth", "dlx_tlx_flit_credit",

            # --- DLX lane interfaces ---
            "ln0_rx_valid", "ln0_rx_header", "ln0_rx_data", "ln0_rx_slip",
            "ln1_rx_valid", "ln1_rx_header", "ln1_rx_data", "ln1_rx_slip",
            "ln2_rx_valid", "ln2_rx_header", "ln2_rx_data", "ln2_rx_slip",
            "ln3_rx_valid", "ln3_rx_header", "ln3_rx_data", "ln3_rx_slip",
            "ln4_rx_valid", "ln4_rx_header", "ln4_rx_data", "ln4_rx_slip",
            "ln5_rx_valid", "ln5_rx_header", "ln5_rx_data", "ln5_rx_slip",
            "ln6_rx_valid", "ln6_rx_header", "ln6_rx_data", "ln6_rx_slip",
            "ln7_rx_valid", "ln7_rx_header", "ln7_rx_data", "ln7_rx_slip",

            "dlx_l0_tx_data", "dlx_l0_tx_header", "dlx_l0_tx_seq",
            "dlx_l1_tx_data", "dlx_l1_tx_header", "dlx_l1_tx_seq",
            "dlx_l2_tx_data", "dlx_l2_tx_header", "dlx_l2_tx_seq",
            "dlx_l3_tx_data", "dlx_l3_tx_header", "dlx_l3_tx_seq",
            "dlx_l4_tx_data", "dlx_l4_tx_header", "dlx_l4_tx_seq",
            "dlx_l5_tx_data", "dlx_l5_tx_header", "dlx_l5_tx_seq",
            "dlx_l6_tx_data", "dlx_l6_tx_header", "dlx_l6_tx_seq",
            "dlx_l7_tx_data", "dlx_l7_tx_header", "dlx_l7_tx_seq",

            # --- Xilinx PHY interface --- 
            "gtwiz_reset_all_out", "gtwiz_reset_rx_datapath_out", "gtwiz_reset_tx_done_in",
            "gtwiz_reset_rx_done_in", "gtwiz_buffbypass_tx_done_in", "gtwiz_buffbypass_rx_done_in",
            "gtwiz_userclk_tx_active_in", "gtwiz_userclk_rx_active_in", "send_first",

            # --- Internal signals (might need some for specific tests) ---
            "rx_tx_crc_error", "rx_tx_retrain", "rx_tx_nack", 
            "rx_tx_tx_ack_rtn", "rx_tx_rx_ack_inc", "rx_tx_tx_ack_ptr_vld", "rx_tx_tx_ack_ptr", 
            "rx_tx_tx_lane_swap", "rx_tx_deskew_done", "rx_tx_linkup", 
            # ... (Add other internal signals if necessary) ...
        ]

        # Call the superclass constructor to initialize the bus
        super().__init__(
            entity=dut,
            name="dlx_bus",
            signals=all_signals,
            optional_signals=[], 
            clock=getattr(dut, clk),  
            reset=getattr(dut, reset),  
            reset_active_level=not active_high_reset,
        )

    # ------------------------------------------------------------
    # Helper functions (example implementations)
    # ------------------------------------------------------------

    async def drive_tlx_flit(self, flit_data, header=0):
        """Drive a flit from the TLX interface to the DLX."""
        self.tlx_dlx_flit_valid.value = 1
        self.tlx_dlx_flit.value = flit_data
        await RisingEdge(self.dut.clk_156_25MHz)
        self.tlx_dlx_flit_valid.value = 0

    async def monitor_dlx_tx(self, expected_flit_data, expected_header):
        """Monitor the DLX TX interface for the expected flit."""
        # This needs to be adapted based on the serialization in ocx_dlx_txdf
        await ClockCycles(self.dut.clk_156_25MHz, 4)  # Wait for serialization

        # ... (Implement data and header checking logic - refer to previous example) ...

    async def drive_dlx_rx(self, flit_data, header=0):
        """Drive a flit onto the DLX RX interface (loopback)."""
        # ... (Implement serialization logic based on ocx_dlx_rxdf) ...

        # ... (Drive lane data and header signals - refer to previous example) ...

    async def monitor_tlx_rx(self):
        """Monitor the TLX interface to receive a flit from DLX."""
        await RisingEdge(self.dlx_tlx_flit_valid)
        received_data = int(self.dlx_tlx_flit.value)
        # ... (Capture header and CRC error status if needed) ...
        return received_data

    # ... (Add more helper functions for control/status, error injection, etc.) ...
