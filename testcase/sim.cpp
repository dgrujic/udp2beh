// DESCRIPTION: Verilator Example: Top level main for invoking model
//
// Copyright 2003-2015 by Wilson Snyder. This program is free software; you can
// redistribute it and/or modify it under the terms of either the GNU
// Lesser General Public License Version 3 or the Perl Artistic License
// Version 2.0.

// Modified to demostrate UDP to Verilog translation


#include <verilated.h>		// Defines common routines
#include "Vsrff_wrap.h"		// From Verilating "test_noprimitives.v"
#if VM_TRACE
# include <verilated_vcd_c.h>	// Trace file format header
#endif

Vsrff_wrap *top;			// Instantiation of module

vluint64_t main_time = 0;	// Current simulation time (64-bit unsigned)

double sc_time_stamp () {	// Called by $time in Verilog
    return main_time;		// Note does conversion to real, to match SystemC
}

int main(int argc, char **argv, char **env) {
    if (0 && argc && argv && env) {}	// Prevent unused variable warnings
    top = new Vsrff_wrap;		// Create instance of module

    Verilated::commandArgs(argc, argv);
    Verilated::debug(0);

#if VM_TRACE			// If verilator was invoked with --trace
    Verilated::traceEverOn(true);	// Verilator must compute traced signals
    VL_PRINTF("Enabling waves...\n");
    VerilatedVcdC* tfp = new VerilatedVcdC;
    top->trace (tfp, 99);	// Trace 99 levels of hierarchy
    tfp->open ("vlt_dump.vcd");	// Open the dump file
#endif

    top->s = 0;		// Set some inputs
    top->r = 0;

	top->eval();		// Evaluate model
#if VM_TRACE
	if (tfp) tfp->dump (main_time);	// Create waveform trace for this timestamp
#endif
	// Read outputs
	VL_PRINTF ("[%" VL_PRI64 "d] %x %x %x\n",
		   main_time, top->s, top->r, top->q);

    main_time++;
    
    top->s = 1;		// Set some inputs
    top->r = 0;

	top->eval();		// Evaluate model
#if VM_TRACE
	if (tfp) tfp->dump (main_time);	// Create waveform trace for this timestamp
#endif
	// Read outputs
	VL_PRINTF ("[%" VL_PRI64 "d] %x %x %x\n",
		   main_time, top->s, top->r, top->q);

    main_time++;


    top->s = 0;		// Set some inputs
    top->r = 0;

	top->eval();		// Evaluate model
#if VM_TRACE
	if (tfp) tfp->dump (main_time);	// Create waveform trace for this timestamp
#endif
	// Read outputs
	VL_PRINTF ("[%" VL_PRI64 "d] %x %x %x\n",
		   main_time, top->s, top->r, top->q);

    main_time++;


    top->s = 0;		// Set some inputs
    top->r = 1;

	top->eval();		// Evaluate model
#if VM_TRACE
	if (tfp) tfp->dump (main_time);	// Create waveform trace for this timestamp
#endif
	// Read outputs
	VL_PRINTF ("[%" VL_PRI64 "d] %x %x %x\n",
		   main_time, top->s, top->r, top->q);

    main_time++;

    top->s = 0;		// Set some inputs
    top->r = 0;

	top->eval();		// Evaluate model
#if VM_TRACE
	if (tfp) tfp->dump (main_time);	// Create waveform trace for this timestamp
#endif
	// Read outputs
	VL_PRINTF ("[%" VL_PRI64 "d] %x %x %x\n",
		   main_time, top->s, top->r, top->q);

    main_time++;

	top->eval();		// Evaluate model
#if VM_TRACE
	if (tfp) tfp->dump (main_time);	// Create waveform trace for this timestamp
#endif
	// Read outputs
	VL_PRINTF ("[%" VL_PRI64 "d] %x %x %x\n",
		   main_time, top->s, top->r, top->q);



    top->final();

#if VM_TRACE
    if (tfp) tfp->close();
#endif

    exit(0L);
}

