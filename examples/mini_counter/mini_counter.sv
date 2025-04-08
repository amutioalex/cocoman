/*-----------------------------------------------------------------------------
// Module: mini_counter
// Description: 
//   A simple clock-cycle counter that counts up to 10 when enabled. 
//   Once the count reaches 10, it asserts the `o_done` signal for one cycle
//   before resetting back to 0.
//
// Parameters:
//   - i_clk   : System clock
//   - i_ena   : Enable signal (starts counting when high)
//   - i_rst_n : Active-low reset
//   - o_done  : Output signal, high for one cycle when count reaches 10
-----------------------------------------------------------------------------*/

`timescale 1ns/1ps

module mini_counter (
    input  logic i_clk,
    input  logic i_ena,
    input  logic i_rst_n,
    output logic o_done
);

  logic [3:0] count;

  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n)
      count <= 4'd0;
    else 
      if (i_ena) begin
        if (count == 4'd9)
          count <= 4'd0;
        else
          count <= count + 4'd1;
      end 
      else
        count <= 4'd0;
  end

  assign o_done = (count == 4'd9);

endmodule : mini_counter
