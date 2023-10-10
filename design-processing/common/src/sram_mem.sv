// Copyright 2023 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

module sram_mem #(
  parameter int Width           = 32, // bit
  parameter int Depth           = 1 << 15,

  parameter bit PreloadELF = 1,
  parameter logic [63:0] RelocateRequestUp = '0,

  // Derived parameters.
  localparam int WidthBytes = Width >> 3,
  localparam int Aw         = $clog2(Depth),
  localparam bit [Aw-1:0] AddrMask = {Aw{1'b1}}
) (
  input  logic             clk_i,
  input  logic             rst_ni,

  input  logic             req_i,
  input  logic             write_i,
  input  logic [Aw-1:0]    addr_i,
  input  logic [Width-1:0] wdata_i,
  input  logic [Width-1:0] wmask_i,
  output logic [Width-1:0] rdata_o
);
  logic [Width-1:0]    mem [bit [31:0]];

  logic [Width-1:0] dbg_addr_masked, dbg_relocated;
  assign dbg_addr_masked = AddrMask & (RelocateRequestUp | addr_i);
  assign dbg_relocated = RelocateRequestUp | addr_i;

  //
  // DPI
  //
  int sections [bit [31:0]];

  import "DPI-C" function read_elf(input string filename);
  import "DPI-C" function byte get_section(output longint address, output longint len);
  import "DPI-C" context function byte read_section(input longint address, inout byte buffer[]);
  import "DPI-C" function string Get_SRAM_ELF_object_filename();

  localparam int unsigned PreloadBufferSize = 100000000;
  initial begin // Load the binary into memory.
    if (PreloadELF) begin
      automatic string binary = Get_SRAM_ELF_object_filename();
      longint section_addr, section_len;
      byte buffer[PreloadBufferSize];
      $display("Loading RAM ELF: %s", binary);
      void'(read_elf(binary));
      while (get_section(section_addr, section_len)) begin
        automatic int num_words = (section_len+(WidthBytes-1))/WidthBytes;
        sections[section_addr/WidthBytes] = num_words;
        // buffer = new [num_words*WidthBytes];
        assert(num_words*WidthBytes <= PreloadBufferSize);
        void'(read_section(section_addr, buffer));

        for (int i = 0; i < num_words; i++) begin
          automatic logic [WidthBytes-1:0][7:0] word = '0;
          for (int j = 0; j < WidthBytes; j++) begin
            word[j] = buffer[i*WidthBytes+j];
            if ($isunknown(word[j]))
              $display("WARNING: Some ELF word is unknown.");
          end
          if (|word)
            $display("Writing ELF word to SRAM addr %x: %x", (AddrMask&section_addr)/WidthBytes+i, word);
          mem[(AddrMask&section_addr)/WidthBytes+i] = word;
          // $display("mem[0x%x]= %x", (AddrMask&section_addr)/WidthBytes+i, mem[(AddrMask&section_addr)/WidthBytes+i]);
        end
      end
    end
  end

  //
  //  Data
  //

  always_ff @(posedge clk_i) begin
		if (req_i) begin
      if (write_i) begin
          rdata_o <= '0;
          for (int i = 0; i < Width; i = i + 1)
            if (wmask_i[i])
              mem[AddrMask & (RelocateRequestUp | addr_i)][i] = wdata_i[i];
      end
      else begin
          if (mem.exists(AddrMask & (RelocateRequestUp | addr_i))) begin
            rdata_o <= mem[AddrMask & (RelocateRequestUp | addr_i)];
            // $display("INFO: Memory known at address %h.", AddrMask & (RelocateRequestUp | addr_i));
          end
          else begin
            rdata_o <= 0;
            // $display("WARNING: Memory unknown at address %h.", AddrMask & (RelocateRequestUp | addr_i));
          end
      end
    end
    else
      rdata_o <= '0;
  end

endmodule
