COCOTB_HDL_TIMEUNIT = ns
COCOTB_HDL_TIMEPRECISION = 1ps

DUT = ocx_dlx_top  # Replace with your top-level module name

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += ./verilog/ocx_dlx_top.v  # Add all your Verilog files here
VERILOG_SOURCES += ./verilog/ocx_dlx_rxdf.v
VERILOG_SOURCES += ./verilog/ocx_dlx_txdf.v
VERILOG_SOURCES += ./verilog/ocx_dlx_xlx_if.v
VERILOG_SOURCES += ./verilog/ocx_bram_infer.v
VERILOG_SOURCES += ./verilog/ocx_dlx_crc.v
VERILOG_SOURCES += ./verilog/ocx_dlx_rx_lane.v
VERILOG_SOURCES += ./verilog/ocx_dlx_rx_lane_66.v
VERILOG_SOURCES += ./verilog/ocx_dlx_rx_main.v
VERILOG_SOURCES += ./verilog/ocx_dlx_tx_ctl.v
VERILOG_SOURCES += ./verilog/ocx_dlx_tx_flt.v
VERILOG_SOURCES += ./verilog/ocx_dlx_tx_gbx.v
VERILOG_SOURCES += ./verilog/ocx_dlx_tx_que.v







# Include cocotb's make rules
include $(shell cocotb-config --makefiles)/Makefile.sim

test:
	@echo "Running tests..."
	$(MAKE) SIM=icarus TOPLEVEL=$(DUT) MODULE=test_ocx_dlx_top  # Update MODULE with your test file name
