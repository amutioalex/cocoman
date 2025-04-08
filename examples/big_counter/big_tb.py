"""A simple testbench for the big_counter module."""

import cocotb
from cocotb.triggers import ClockCycles
from tb_utils import setup_dut


@cocotb.test()
async def count_once(dut) -> None:
    """Test: Runs the counter for 100 cycles and asserts o_done at the correct moment."""
    clk_cr = await setup_dut(dut)

    dut.i_ena.value = 1
    await ClockCycles(dut.i_clk, 99)
    assert dut.o_done.value == 0, "Error: o_done asserted too early!"

    await ClockCycles(dut.i_clk, 1)
    assert dut.o_done.value == 1, "Error: o_done did not assert at 100 cycles!"

    await ClockCycles(dut.i_clk, 10)
    assert dut.o_done.value == 0, "Error: o_done did not reset after cycle 100!"

    clk_cr.cancel()
