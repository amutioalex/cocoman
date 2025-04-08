/*-----------------------------------------------------------------------------
// Module: big_counter
// Description: 
//   A hierarchical counter that counts 100 clock cycles before asserting the
//   `o_done` signal for 10 cycles. It instantiates `mini_counter` to count
//   groups of 10 cycles.
//
// Parameters:
//   - i_clk   : System clock
//   - i_ena   : Enable signal (starts counting when high)
//   - i_rst_n : Active-low reset
//   - o_done  : Output signal, high for one cycle when count reaches 100
-----------------------------------------------------------------------------*/

module big_counter (
  input  logic i_clk,
  input  logic i_ena,
  input  logic i_rst_n,
  output logic o_done
);

  logic [3:0] x_count;
  logic       x_min_done;

  mini_counter min_c (
    .i_clk(i_clk),
    .i_ena(i_ena),
    .i_rst_n(i_rst_n),
    .o_done(x_min_done)
  );

  always @(posedge x_min_done or negedge i_rst_n) begin
    if (!i_rst_n)
      x_count <= 4'd0;
    else 
      if (i_ena) begin
        if (x_count != 4'd10)
          x_count <= x_count + 4'd1;
        else
          x_count <= 4'd0;
      end 
      else
        x_count <= 4'd0;
  end

  assign o_done = (x_count == 4'd10);

endmodule : big_counter
