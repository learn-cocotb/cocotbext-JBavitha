"""Testbench for the ocx_dlx_top module.

This module contains cocotb-based tests for verifying the functionality
of the ocx_dlx_top design using external driver and monitor modules.
"""
import secrets

import cocotb
from cocotb.clock import Clock
from cocotb.handle import SimHandle
from cocotb.triggers import ClockCycles, RisingEdge, Timer
from driver import DLXDriver
from monitor import DLXMonitor


@cocotb.test()
async def dlx_test(dut:SimHandle) -> None:
    """Comprehensive testbench for ocx_dlx_top module."""
    cocotb.log.info("Starting DLX testbench")

    # Instantiate driver and monitor
    driver = DLXDriver(dut, dut.clk_156_25MHz, dut.dlx_reset)
    monitor = DLXMonitor(dut, dut.clk_156_25MHz)

    # Clock generation (156.25 MHz)
    cocotb.log.info("Starting clock generation")
    clock = Clock(dut.clk_156_25MHz, 10, units="ns")
    cocotb.start_soon(clock.start())
    cocotb.log.info("Clock started")

    # Reset sequence (refer to ocx_dlx_xlx_if for accurate timing)
    dut.hb_gtwiz_reset_all_in.value = 1
    dut.send_first.value = 0
    cocotb.log.info("Applying reset sequence")
    await RisingEdge(dut.clk_156_25MHz)
    await Timer(100, units="ns")  # Hold reset for a short duration

    dut.gtwiz_reset_tx_done_in.value = 1
    dut.gtwiz_reset_rx_done_in.value = 1
    await RisingEdge(dut.clk_156_25MHz)

    dut.gtwiz_buffbypass_tx_done_in.value = 1
    dut.gtwiz_buffbypass_rx_done_in.value = 1
    await RisingEdge(dut.clk_156_25MHz)

    dut.gtwiz_userclk_tx_active_in.value = 1
    dut.gtwiz_userclk_rx_active_in.value = 1
    await RisingEdge(dut.clk_156_25MHz)

    dut.send_first.value = 1
    await RisingEdge(dut.clk_156_25MHz)
    dut.hb_gtwiz_reset_all_in.value = 0
    cocotb.log.info("Reset sequence completed")
    await RisingEdge(dut.clk_156_25MHz)

    # Wait for linkup
    cocotb.log.info("Waiting for linkup signal")
    timeout = 5000  # Increased timeout duration
    start_time = cocotb.utils.get_sim_time("ns")
    while dut.rx_tx_linkup.value != 1:
        await RisingEdge(dut.clk_156_25MHz)
        if cocotb.utils.get_sim_time("ns") - start_time > timeout:
            raise RuntimeError(f"Link-up signal not asserted within {timeout}ns")

        # Debug: Log rx_tx_linkup signal
        cocotb.log.info(f"Current value of rx_tx_linkup: {dut.rx_tx_linkup.value}")
    cocotb.log.info("DLX link is up")

    # ------------------------------------------------------------
    # Test Cases
    # ------------------------------------------------------------

    # --- Basic Data Transfer ---
    cocotb.log.info("Testing basic data transfer")
    await run_data_transfer_test(driver, monitor, 10)  # Send 10 flits

    # --- Flow Control ---
    cocotb.log.info("Testing flow control")
    await run_flow_control_test(driver, monitor)

    # --- CRC Errors ---
    cocotb.log.info("Testing CRC error injection")
    await run_crc_error_test(driver, monitor, 5)

    # --- Lane Errors ---
    cocotb.log.info("Testing lane errors")
    await run_lane_error_test(driver, monitor)

    # --- NACK and Retransmission ---
    cocotb.log.info("Testing NACK and retransmission")
    await run_nack_retransmission_test(driver, monitor)

    # --- Random Stress Test ---
    cocotb.log.info("Running random stress test")
    await run_random_stress_test(driver, monitor, 100)

    cocotb.log.info("DLX testbench completed")

# ------------------------------------------------------------
# Helper Functions for Test Cases
# ------------------------------------------------------------

async def run_data_transfer_test(driver: DLXDriver, monitor: DLXMonitor, num_flits: int) -> None:
    """Test basic data transfer from TLX to DLX and back."""
    for _ in range(num_flits):
        flit_data = secrets.randbelow(2**512)
        header = secrets.randbelow(4)

        # Send flit using driver
        await driver.send_tlx_flit(flit_data, header)

        # Check TX output using monitor
        await monitor.check_dlx_tx_output(flit_data, header)

        # Send flit to DLX RX (loopback)
        await driver.send_dlx_flit(flit_data, header)

        # Check RX output using monitor
        await monitor.check_tlx_rx_output(flit_data, header)


async def run_flow_control_test(driver: DLXDriver, monitor: DLXMonitor) -> None:
    """Test credit-based flow control."""
    for _ in range(10):
        flit_data = secrets.randbelow(2**512)
        await driver.send_tlx_flit(flit_data, 0)
        await ClockCycles(driver.dut.clk_156_25MHz, 1)

    await Timer(100, units="ns")
    assert driver.dut.dlx_tlx_flit_credit.value == 0, "Flow control not working (credit not 0)"

    while driver.dut.dlx_tlx_flit_credit.value == 0:
        await RisingEdge(driver.dut.clk_156_25MHz)

    cocotb.log.info("Flow control working: Credits recovered")

    for _ in range(5):
        flit_data = secrets.randbelow(2**512)
        await driver.send_tlx_flit(flit_data, 0)
        await monitor.check_dlx_tx_output(flit_data, 0)


async def run_crc_error_test(driver: DLXDriver, monitor: DLXMonitor, num_flits: int) -> None:
    """Inject CRC errors and verify detection."""
    for _ in range(num_flits):
        flit_data = secrets.randbelow(2**512)
        await driver.send_tlx_flit(flit_data, 0)

        corrupted_data = driver.dut.ln0_rx_data.value ^ 0x0F
        await Timer(1, units="ns")
        driver.dut.ln0_rx_data.value = corrupted_data

        await RisingEdge(driver.dut.dlx_tlx_flit_valid)
        assert driver.dut.dlx_tlx_flit_crc_err.value == 1, "CRC error not detected"
        assert driver.dut.dlx_tlx_flit.value != flit_data, "Corrupted flit passed to TLX"


async def run_lane_error_test(driver: DLXDriver, monitor: DLXMonitor) -> None:
    """Simulate lane errors (e.g., lane down)."""
    driver.dut.ln0_rx_valid.value = 0
    await Timer(100, units="ns")

    flit_data = secrets.randbelow(2**512)
    await driver.send_tlx_flit(flit_data, 0)
    await monitor.check_dlx_tx_output(flit_data, 0)

    driver.dut.ln3_rx_valid.value = 0
    await Timer(100, units="ns")

    flit_data = secrets.randbelow(2**512)
    await driver.send_tlx_flit(flit_data, 0)


async def run_nack_retransmission_test(driver: DLXDriver, monitor: DLXMonitor) -> None:
    """Test NACK and flit retransmission."""
    flit_data = secrets.randbelow(2**512)
    await driver.send_tlx_flit(flit_data, 0)

    driver.dut.rx_tx_nack.value = 1
    await RisingEdge(driver.dut.clk_156_25MHz)
    driver.dut.rx_tx_nack.value = 0

    await monitor.check_dlx_tx_output(flit_data, 0)


async def run_random_stress_test(driver: DLXDriver, monitor: DLXMonitor, num_flits: int) -> None:
    """Send random data with random errors."""
    for _ in range(num_flits):
        flit_data = secrets.randbelow(2**512)
        header = secrets.randbelow(4)
        await driver.send_tlx_flit(flit_data, header)

        if secrets.randbelow(10) < 1:
            error_type = secrets.choice(["crc", "lane", "nack"])
            if error_type == "crc":
                lane_num = secrets.randbelow(8)
                corrupted_data = getattr(driver.dut, f"ln{lane_num}_rx_data").value ^ 0xFF
                setattr(driver.dut, f"ln{lane_num}_rx_data", corrupted_data)
            elif error_type == "lane":
                lane_num = secrets.randbelow(8)
                getattr(driver.dut, f"ln{lane_num}_rx_valid").value = 0
            elif error_type == "nack":
                driver.dut.rx_tx_nack.value = 1
                await RisingEdge(driver.dut.clk_156_25MHz)
                driver.dut.rx_tx_nack.value = 0
