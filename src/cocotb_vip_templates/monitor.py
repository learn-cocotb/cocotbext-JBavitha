"""Driver for the ocx_dlx_top module, handling the TLX and DLX interfaces."""
from typing import List, Protocol

from cocotb.handle import SimHandleBase
from cocotb.triggers import ClockCycles, RisingEdge


class DUTInterface(Protocol):
    """Protocol defining the required attributes of the DUT for the monitor."""

    # TLX RX interface signals
    dlx_tlx_flit_valid: SimHandleBase
    dlx_tlx_flit: SimHandleBase
    dlx_tlx_flit_crc_err: SimHandleBase

    # DLX TX lane signals
    dlx_l0_tx_data: SimHandleBase
    dlx_l0_tx_header: SimHandleBase
    dlx_l1_tx_data: SimHandleBase
    dlx_l1_tx_header: SimHandleBase
    dlx_l2_tx_data: SimHandleBase
    dlx_l2_tx_header: SimHandleBase
    dlx_l3_tx_data: SimHandleBase
    dlx_l3_tx_header: SimHandleBase
    dlx_l4_tx_data: SimHandleBase
    dlx_l4_tx_header: SimHandleBase
    dlx_l5_tx_data: SimHandleBase
    dlx_l5_tx_header: SimHandleBase
    dlx_l6_tx_data: SimHandleBase
    dlx_l6_tx_header: SimHandleBase
    dlx_l7_tx_data: SimHandleBase
    dlx_l7_tx_header: SimHandleBase


class DLXMonitor:
    """Monitor for ocx_dlx_top."""

    def __init__(self, dut: DUTInterface, clk_signal: SimHandleBase):
        """Initialize the DLX monitor with the DUT and clock signal."""
        self.dut = dut
        self.clk_signal = clk_signal

    async def observe_tlx_rx_flit(self) -> tuple:
        """Observe flits received on TLX RX interface.

        Returns:
            tuple: The flit data, header, and CRC error flag.
        """
        await RisingEdge(self.dut.dlx_tlx_flit_valid)
        flit = int(self.dut.dlx_tlx_flit.value)
        crc_error = int(self.dut.dlx_tlx_flit_crc_err.value)
        header = int(self.dut.dlx_tlx_flit_crc_err.value)  # Adjust this if header is separate
        return flit, header, crc_error

    async def check_lane_outputs(self, expected_data: List[int], expected_header: List[int]) -> None:
        """Check the serialized output on DLX TX lanes.

        Args:
            expected_data (List[int]): The expected data for each lane.
            expected_header (List[int]): The expected header for each lane.

        Raises:
            ValueError: If the observed data or header does not match the expected values.
        """
        await ClockCycles(self.clk_signal, 4)  # Adjust based on serialization delay
        for i in range(8):
            lane_data = int(getattr(self.dut, f"dlx_l{i}_tx_data").value)
            lane_header = int(getattr(self.dut, f"dlx_l{i}_tx_header").value)
            if lane_data != expected_data[i]:
                raise ValueError(f"Lane {i} data mismatch: Expected {expected_data[i]}, but got {lane_data}")
            if lane_header != expected_header[i]:
                raise ValueError(f"Lane {i} header mismatch: Expected {expected_header[i]}, but got {lane_header}")
