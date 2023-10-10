module clk_rst_gen #(
    parameter time      CLK_PERIOD,
    parameter unsigned  RST_CLK_CYCLES
) (
    output logic clk_o,
    output logic rst_no
);

    timeunit 1ns;
    timeprecision 10ps;

    logic clk;

    // Clock Generation
    initial begin
        clk = 1'b0;
    end
    always begin
        #(CLK_PERIOD/2);
        clk = ~clk;
    end
    assign clk_o = clk;

    // Reset Generation
    rst_gen #(
        .RST_CLK_CYCLES (RST_CLK_CYCLES)
    ) i_rst_gen (
        .clk_i  (clk),
        .rst_ni (1'b1),
        .rst_o  (),
        .rst_no (rst_no)
    );

endmodule
