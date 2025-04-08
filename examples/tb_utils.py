"""A library module containing common testbench functions."""

from cocotb import start_soon
from cocotb.clock import Clock
from cocotb.task import Task
from cocotb.triggers import ClockCycles


async def setup_dut(dut) -> Task:
    """Initializes the DUT signals and starts the clock."""
    clk_cr = start_soon(Clock(dut.i_clk, 2, "ns").start(start_high=False))
    dut.i_rst_n.value = 0
    dut.i_ena.value = 0
    await ClockCycles(dut.i_clk, 2)
    dut.i_rst_n.value = 1
    return clk_cr
