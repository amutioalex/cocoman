"""A simple testbench for the mini_counter module."""

import cocotb
from cocotb.triggers import ClockCycles
from tb_utils import setup_dut


@cocotb.test()
async def count_once(dut) -> None:
    """Test: Counts to 10 once and asserts o_done at the correct moment."""
    clk_cr = await setup_dut(dut)

    dut.i_ena.value = 1
    await ClockCycles(dut.i_clk, 9)
    assert dut.o_done.value == 0, "Error: o_done asserted too early"

    await ClockCycles(dut.i_clk, 1)
    assert dut.o_done.value == 1, "Error: o_done did not assert at count=10"

    await ClockCycles(dut.i_clk, 1)
    assert dut.o_done.value == 0, "Error: o_done did not reset after cycle 10"

    clk_cr.cancel()


@cocotb.test()
async def count_twice(dut) -> None:
    """Test: Counts to 10 twice and asserts o_done correctly both times."""
    clk_cr = await setup_dut(dut)

    dut.i_ena.value = 1
    for i in range(2):
        wait_cycles = 9 if i == 0 else 8
        await ClockCycles(dut.i_clk, wait_cycles)
        assert dut.o_done.value == 0, "Error: o_done asserted too early!"

        await ClockCycles(dut.i_clk, 1)
        assert dut.o_done.value == 1, "Error: o_done did not assert at count=10!"

        await ClockCycles(dut.i_clk, 1)
        assert dut.o_done.value == 0, "Error: o_done did not reset after cycle 10!"

    clk_cr.cancel()
