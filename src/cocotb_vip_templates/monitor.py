"""Driver for the ocx_dlx_top module, handling the TLX and DLX interfaces."""
from typing import List

from cocotb.triggers import ClockCycles, RisingEdge


class DLXMonitor:
    """Monitor for ocx_dlx_top."""

    def __init__(self, dut: object, clk_signal: object):
        """Initialize the DLX monitor with the DUT and clock signal."""
        self.dut = dut
        self.clk_signal = clk_signal

    async def observe_tlx_rx_flit(self) -> None:
        """Observe flits received on TLX RX interface."""
        await RisingEdge(self.dut.dlx_tlx_flit_valid)
        flit = int(self.dut.dlx_tlx_flit.value)
        crc_error = int(self.dut.dlx_tlx_flit_crc_err.value)  # Separate CRC error flag
        header = int(self.dut.dlx_tlx_flit_crc_err.value)  # If header is actually the same as CRC, adjust this line
        return flit, header, crc_error

    async def check_lane_outputs(self, expected_data: List[int], expected_header: List[int]) -> None:
        """Check the serialized output on DLX TX lanes."""
        await ClockCycles(self.clk_signal, 4)  # Adjust based on serialization delay
        for i in range(8):
            lane_data = int(getattr(self.dut, f"dlx_l{i}_tx_data").value)
            lane_header = int(getattr(self.dut, f"dlx_l{i}_tx_header").value)
            if lane_data != expected_data[i]:
                raise ValueError(f"Lane {i} data mismatch: Expected {expected_data[i]}, but got {lane_data}")
            if lane_header != expected_header[i]:
                raise ValueError(f"Lane {i} header mismatch: Expected {expected_header[i]}, but got {lane_header}")
