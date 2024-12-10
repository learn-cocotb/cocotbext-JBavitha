"""Driver module for the ocx_dlx_top module in the cocotb verification framework.

This module provides a `DLXDriver` class for interacting with the TLX and DLX interfaces of the DUT.
"""

import cocotb
from cocotb.handle import SimHandleBase
from cocotb.triggers import RisingEdge


class DUTInterface:
    """Defines the signals in the DUT interface."""

    # Clock and reset signals
    clk_156_25_mhz: SimHandleBase
    reset: SimHandleBase

    # RX interface signals
    rx_tx_linkup: SimHandleBase
    ln0_rx_data: SimHandleBase
    ln0_rx_header: SimHandleBase
    ln0_rx_valid: SimHandleBase
    ln1_rx_data: SimHandleBase
    ln1_rx_header: SimHandleBase
    ln1_rx_valid: SimHandleBase
    # Repeat similar attributes for ln2 to ln7 signals

    # TX interface signals
    tlx_dlx_flit_valid: SimHandleBase
    tlx_dlx_flit: SimHandleBase
    tlx_dlx_debug_encode: SimHandleBase
    tlx_dlx_debug_info: SimHandleBase

    # Additional internal signals, if needed


class DLXDriver:
    """Driver for the ocx_dlx_top module, handling the TLX and DLX interfaces."""

    def __init__(self, dut: DUTInterface) -> None:
        """Initialize the DLX driver.

        Args:
            dut: The top-level design under test (DUT).
        """
        self.dut = dut
        self.clk_signal = dut.clk_156_25_mhz
        self.reset_signal = dut.reset
        cocotb.log.info("DLXDriver initialized")

    async def apply_reset_sequence(self) -> None:
        """Apply a reset to the DUT."""
        cocotb.log.info("Applying reset sequence")
        self.reset_signal.value = 1
        await RisingEdge(self.clk_signal)  # Hold reset for one cycle
        await RisingEdge(self.clk_signal)  # Hold reset for two cycles
        self.reset_signal.value = 0
        cocotb.log.info("Reset deasserted, waiting for initialization")
        await RisingEdge(self.clk_signal)  # Wait for one clock cycle after deassertion

    async def wait_for_linkup(self, timeout_ns: int = 1000) -> None:
        """Wait for the rx_tx_linkup signal to be asserted (1), with a timeout.

        Args:
            timeout_ns (int): Timeout in nanoseconds for waiting.
        """
        clock_period_ns = 1 / (self.clk_signal.frequency / 1e9)  # Convert frequency to period in ns
        timeout_ticks = timeout_ns // clock_period_ns
        timeout_count = 0
        cocotb.log.info("Waiting for linkup signal")

        while self.dut.rx_tx_linkup.value != 1 and timeout_count < timeout_ticks:
            await RisingEdge(self.clk_signal)
            timeout_count += 1

        if timeout_count >= timeout_ticks:
            cocotb.log.error("Timeout waiting for linkup signal to assert")
        else:
            cocotb.log.info("Linkup signal asserted")

    async def send_tlx_flit(self, flit_data: int, header: int) -> None:
        """Drive a flit to the TLX input interface of the DUT.

        Args:
            flit_data (int): 512-bit flit data to send.
            header (int): Header information.
        """
        self.dut.tlx_dlx_flit_valid.value = 1
        self.dut.tlx_dlx_flit.value = flit_data
        self.dut.tlx_dlx_debug_encode.value = header  # If applicable
        await RisingEdge(self.clk_signal)
        self.dut.tlx_dlx_flit_valid.value = 0

    async def send_dlx_flit(self, flit_data: int, header: int) -> None:
        """Drive a flit to the DLX RX input interface (split across lanes).

        Args:
            flit_data (int): 512-bit flit data to distribute across lanes.
            header (int): Header information for each lane.
        """
        # Split the 512-bit flit data into 8 64-bit chunks
        data_chunks = [(flit_data >> (i * 64)) & 0xFFFFFFFFFFFFFFFF for i in range(8)]
        for i, data in enumerate(data_chunks):
            getattr(self.dut, f"ln{i}_rx_data").value = data
            getattr(self.dut, f"ln{i}_rx_header").value = header
            getattr(self.dut, f"ln{i}_rx_valid").value = 1
        await RisingEdge(self.clk_signal)
        # Reset valid signals after sending
        for i in range(8):
            getattr(self.dut, f"ln{i}_rx_valid").value = 0
