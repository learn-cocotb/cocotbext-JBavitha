"""Testbench for the ocx_dlx_top module.

This module contains cocotb-based tests for verifying the functionality
of the ocx_dlx_top design.
"""
import random
import secrets

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer
@cocotb.test()
async def dlx_test(dut: cocotb.SimHandle) -> None:
    """Comprehensive testbench for ocx_dlx_top module."""
    cocotb.log.info("Starting DLX testbench")

    # Clock generation (156.25 MHz)
    clock = Clock(dut.clk_156_25MHz, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset sequence (refer to ocx_dlx_xlx_if for accurate timing)
    dut.hb_gtwiz_reset_all_in.value = 1
    dut.send_first.value = 0
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
    await RisingEdge(dut.clk_156_25MHz)


    # Wait for linkup
    while dut.rx_tx_linkup.value != 1:
        await RisingEdge(dut.clk_156_25MHz)
    cocotb.log.info("DLX link is up")

    # ------------------------------------------------------------
    # Test Cases
    # ------------------------------------------------------------

    # --- Basic Data Transfer ---
    cocotb.log.info("Testing basic data transfer")
    await run_data_transfer_test(dut, 10)  # Send 10 flits

    # --- Flow Control ---
    cocotb.log.info("Testing flow control")
    await run_flow_control_test(dut)

    # --- CRC Errors ---
    cocotb.log.info("Testing CRC error injection")
    await run_crc_error_test(dut, 5)

    # --- Lane Errors ---
    cocotb.log.info("Testing lane errors")
    await run_lane_error_test(dut)

    # --- NACK and Retransmission ---
    cocotb.log.info("Testing NACK and retransmission")
    await run_nack_retransmission_test(dut)

    # --- Random Stress Test ---
    cocotb.log.info("Running random stress test")
    await run_random_stress_test(dut, 100)

    cocotb.log.info("DLX testbench completed")

# ------------------------------------------------------------
# Helper Functions for Test Cases
# ------------------------------------------------------------

async def run_data_transfer_test(dut: cocotb.SimHandle, num_flits: int) -> None:
    """Test basic data transfer from TLX to DLX and back."""
    for _ in range(num_flits):
        flit_data = secrets.randbelow(2**512)  # Generates a value between 0 and 2^512-1
        header = secrets.randbelow(4)  # Generates a value between 0 and 3

        # TLX to DLX
        await send_tlx_flit(dut, flit_data, header)
        await check_dlx_tx_output(dut, flit_data, header)

        # DLX to TLX (loopback - connect DLX TX to DLX RX)
        await send_dlx_flit(dut, flit_data, header)
        await check_tlx_rx_output(dut, flit_data, header)


async def run_flow_control_test(dut: cocotb.SimHandle) -> None:
    """Test credit-based flow control."""
    # Send flits faster than the receiver can handle
    for _ in range(10):
        flit_data = secrets.randbelow(2**512)
        await send_tlx_flit(dut, flit_data, 0)
        await ClockCycles(dut.clk_156_25MHz, 1) 

    # Monitor dlx_tlx_flit_credit to ensure it goes low (no credits)
    await Timer(100, units="ns")
    assert dut.dlx_tlx_flit_credit.value == 0, "Flow control not working (credit not 0)"

    # Wait for credits to become available again
    while dut.dlx_tlx_flit_credit.value == 0:
        await RisingEdge(dut.clk_156_25MHz)
    cocotb.log.info("Flow control working: Credits recovered")

    # Send more flits to check if data is transferred correctly after backpressure
    for _ in range(5):
        flit_data = secrets.randbelow(2**512)  # Cryptographically secure random number
        await send_tlx_flit(dut, flit_data, 0)
        await check_dlx_tx_output(dut, flit_data, 0)  # Check TX output


async def run_crc_error_test(dut: cocotb.SimHandle, num_flits: int) -> None:
    """Inject CRC errors and verify detection."""
    for _ in range(num_flits):
        flit_data = secrets.randbelow(2**512)  # Cryptographically secure random number
        await send_tlx_flit(dut, flit_data, 0)

        # Corrupt data on lane 0 (example) - flip a few bits
        corrupted_data = dut.ln0_rx_data.value ^ 0x0F 
        dut.ln0_rx_data.value = corrupted_data

        # Wait for flit reception and check for CRC error
        await RisingEdge(dut.dlx_tlx_flit_valid)
        assert dut.dlx_tlx_flit_crc_err.value == 1, "CRC error not detected"

        # Check that the corrupted flit is NOT propagated to TLX
        assert dut.dlx_tlx_flit.value != flit_data, "Corrupted flit passed to TLX"

        # ... (Add checks for error handling and recovery) ...


async def run_lane_error_test(dut: cocotb.SimHandle) -> None:
    """Simulate lane errors (e.g., lane down)."""
    # Bring down lane 0
    dut.ln0_rx_valid.value = 0
    await Timer(100, units="ns")

    # Send a flit and check if it's still received (other lanes should compensate)
    flit_data = secrets.randbelow(2**512)  # Cryptographically secure random number
    await send_tlx_flit(dut, flit_data, 0)
    await check_dlx_tx_output(dut, flit_data, 0)  # Check TX output

    # Bring down lane 3 as well
    dut.ln3_rx_valid.value = 0
    await Timer(100, units="ns")

    # Send another flit (might be dropped or have errors depending on DLX config)
    flit_data = random.randint(0, (2**512) - 1)
    await send_tlx_flit(dut, flit_data, 0)

    # ... (Add checks for error handling, recovery, or potential data loss) ...


async def run_nack_retransmission_test(dut):
    """Test NACK and flit retransmission."""
    flit_data = secrets.randbelow(2**512)  # Cryptographically secure random number
    await send_tlx_flit(dut, flit_data, 0)

    # Force a NACK by manipulating ACK signals (example)
    dut.rx_tx_nack.value = 1
    await RisingEdge(dut.clk_156_25MHz)
    dut.rx_tx_nack.value = 0

    # Check for retransmission of the flit (might need to monitor TX output)
    await check_dlx_tx_output(dut, flit_data, 0)  # Assuming loopback


async def run_random_stress_test(dut: cocotb.SimHandle, num_flits: int) -> None:
    """Send random data with random errors."""
    for _ in range(num_flits):
        flit_data = random.randint(0, (2**512) - 1)
        header = random.randint(0, 3)
        await send_tlx_flit(dut, flit_data, header)

        # Introduce random errors (CRC, lane errors, NACK)
        if random.random() < 0.1:  # 10% chance of error
            error_type = random.choice(["crc", "lane", "nack"])
            if error_type == "crc":
                # Corrupt data on a random lane
                lane_num = random.randint(0, 7)
                corrupted_data = getattr(dut, f"ln{lane_num}_rx_data").value ^ 0xFF
                setattr(dut, f"ln{lane_num}_rx_data", corrupted_data)
            elif error_type == "lane":
                # Bring down a random lane
                lane_num = random.randint(0, 7)
                getattr(dut, f"ln{lane_num}_rx_valid").value = 0
            elif error_type == "nack":
                # Force a NACK
                dut.rx_tx_nack.value = 1
                await RisingEdge(dut.clk_156_25MHz)
                dut.rx_tx_nack.value = 0

        # ... (Monitor and check for correct behavior or errors) ...


# --- Helper Functions for Stimulus and Checking ---

async def send_tlx_flit(dut, flit_data, header):
    """Send a flit from the TLX interface."""
    dut.tlx_dlx_flit_valid.value = 1
    dut.tlx_dlx_flit.value = flit_data
    # ... (Set any other relevant TLX signals) ...
    await RisingEdge(dut.clk_156_25MHz)
    dut.tlx_dlx_flit_valid.value = 0

async def check_dlx_tx_output(dut, flit_data, header):
    """Check the DLX TX output for the sent flit."""
    # This function needs to be adapted based on the serialization scheme
    # in the ocx_dlx_txdf module. Here's a basic example:

    await ClockCycles(dut.clk_156_25MHz, 4) # Wait for serialization (adjust as needed)

    # Assuming flit_data is serialized across lanes in 64-bit chunks
    expected_data = []
    for i in range(8):  # 8 lanes
        start_bit = i * 64
        end_bit = start_bit + 64
        expected_data.append(flit_data >> start_bit & 0xFFFFFFFFFFFFFFFF)

    # Compare expected data with the output of each lane
    for i in range(8):
        lane_data = getattr(dut, f"dlx_l{i}_tx_data").value.integer
        assert lane_data == expected_data[i], f"Data mismatch on lane {i}"

    # Check header values (assuming they are sent on the first cycle)
    for i in range(8):
        lane_header = getattr(dut, f"dlx_l{i}_tx_header").value.integer
        # ... (Compare lane_header with the expected header value for this lane) ...


async def send_dlx_flit(dut, flit_data, header):
    """Send a flit to the DLX RX interface (loopback)."""
    # This function needs to serialize the data and header across the lanes
    # according to the deserialization scheme in ocx_dlx_rxdf.

    # Example (adjust based on actual serialization):
    data_chunks = []
    for i in range(8):
        start_bit = i * 64
        end_bit = start_bit + 64
        data_chunks.append(flit_data >> start_bit & 0xFFFFFFFFFFFFFFFF)

    # Drive the lane data and header signals
    for i in range(8):
        getattr(dut, f"ln{i}_rx_data").value = data_chunks[i]
        getattr(dut, f"ln{i}_rx_header").value = header  # Or calculate header per lane
        getattr(dut, f"ln{i}_rx_valid").value = 1

    await RisingEdge(dut.clk_156_25MHz)

    # De-assert valid signals
    for i in range(8):
        getattr(dut, f"ln{i}_rx_valid").value = 0


async def check_tlx_rx_output(dut, flit_data, header):
    """Check the TLX interface for the received flit."""
    await RisingEdge(dut.dlx_tlx_flit_valid)
    received_data = int(dut.dlx_tlx_flit.value)
    assert received_data == flit_data, "Data mismatch on TLX reception"
    # ... (Compare received header with expected header) ...
