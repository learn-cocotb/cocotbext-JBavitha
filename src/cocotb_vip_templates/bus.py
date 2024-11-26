"""Bus."""
import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb_bus.bus import Bus as BusBaseClass


class Bus:
    """Bus class to abstract and interact with signals in the ocx_dlx_top module."""

    def __init__(
        self,
        dut: cocotb.SimHandle,
        prefix: str = "",
        suffix: str = "",
        bus_separator: str = "_",
        clk: str = "clk",
        reset: str = "rst_n",
        active_high_reset: bool = True,
        uppercase: bool = False,
    ):
        """Constructor for Bus class.

        Args:
            dut (SimHandle): DUT top-level handle.
            prefix (str): Prefix for signal names.
            suffix (str): Suffix for signal names.
            bus_separator (str): Separator between prefix/suffix and signal names.
            clk (str): Name of the clock signal.
            reset (str): Name of the reset signal.
            active_high_reset (bool): Whether the reset is active high.
            uppercase (bool): Whether signal names are uppercase.
        """
        self.dut = dut
        self.prefix = prefix
        self.suffix = suffix
        self.bus_separator = bus_separator
        self.clk = getattr(dut, clk)
        self.reset = getattr(dut, reset)
        self.active_high_reset = active_high_reset
        self.uppercase = uppercase

        # Initialize signal groups
        self.rx_signals = {}
        self.tx_signals = {}
        self.rx_lanes = {}
        self.tx_lanes = {}

        # Automatically map signals
        self.map_rx_signals()
        self.map_tx_signals()
        self.map_rx_lanes()
        self.map_tx_lanes()

    def map_rx_signals(self) -> None:
        """Map RX interface signals."""
        self.rx_signals = {
            "flit_valid": self.dut.dlx_tlx_flit_valid,
            "flit": self.dut.dlx_tlx_flit,
            "crc_err": self.dut.dlx_tlx_flit_crc_err,
            "link_up": self.dut.dlx_tlx_link_up,
            "config_info": self.dut.dlx_config_info,
        }

    def map_tx_signals(self) -> None:
        """Map TX interface signals."""
        self.tx_signals = {
            "flit_valid": self.dut.tlx_dlx_flit_valid,
            "flit": self.dut.tlx_dlx_flit,
            "debug_encode": self.dut.tlx_dlx_debug_encode,
            "debug_info": self.dut.tlx_dlx_debug_info,
        }

    def map_rx_lanes(self):
        """Map RX lanes dynamically."""
        for i in range(8):  # Assuming 8 RX lanes (ln0 to ln7)
            self.rx_lanes[f"lane{i}"] = {
                "valid": getattr(self.dut, f"ln{i}_rx_valid"),
                "header": getattr(self.dut, f"ln{i}_rx_header"),
                "data": getattr(self.dut, f"ln{i}_rx_data"),
                "slip": getattr(self.dut, f"ln{i}_rx_slip"),
            }

    def map_tx_lanes(self):
        """Map TX lanes dynamically."""
        for i in range(8):  # Assuming 8 TX lanes (l0 to l7)
            self.tx_lanes[f"lane{i}"] = {
                "data": getattr(self.dut, f"dlx_l{i}_tx_data"),
                "header": getattr(self.dut, f"dlx_l{i}_tx_header"),
                "seq": getattr(self.dut, f"dlx_l{i}_tx_seq"),
            }

    async def reset_dut(self, duration: int = 10):
        """Toggle the reset signal for the specified duration."""
        cocotb.log.info(f"Resetting DUT for {duration} ns...")
        self.reset <= 1 if self.active_high_reset else 0
        await Timer(duration, units="ns")
        self.reset <= 0 if self.active_high_reset else 1
        cocotb.log.info("Reset complete.")

    async def wait_for_clock_cycles(self, cycles: int):
        """Wait for a specified number of clock cycles."""
        for _ in range(cycles):
            await RisingEdge(self.clk)

    async def wait_for_link_up(self):
        """Wait until the link is established."""
        cocotb.log.info("Waiting for the link to come up...")
        while not self.rx_signals["link_up"].value:
            await RisingEdge(self.clk)
        cocotb.log.info("Link is up.")

    def get_bus(self) -> BusBaseClass:
        """Creates and returns a generic bus object."""
        return BusBaseClass()

    def get_somespecialfunction_bus(self, params: int) -> BusBaseClass:
        """Handles special signal naming conventions and returns the bus."""
        cocotb.log.info(f"Special handling for parameter: {params}")
        return BusBaseClass()

    def record_coverage(self):
        """Record functional coverage."""
        # Example: Add coverage points for RX and TX flits
        rx_flit_valid = self.rx_signals["flit_valid"].value
        tx_flit_valid = self.tx_signals["flit_valid"].value
        cocotb.log.info(f"Coverage: RX flit valid = {rx_flit_valid}, TX flit valid = {tx_flit_valid}")

