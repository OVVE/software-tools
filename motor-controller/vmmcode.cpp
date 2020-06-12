// nanoJ Configuration for Nanotec CL4-E Motor Controller

// CiA 402 Power State Machine
map U16 ControlWord as output 0x6040:00
map U16 StatusWord  as input  0x6041:00

#include "wrapper.h"

// Motor: ST6018D4508
// Motor Maximum Current: 6.36 A (parallel)
// Motor Maximum Torque: 3.56 N-m (24V parallel)
//
// Gearbox: GP56-T2-26-HR
// Gearbox Reduction Ratio: 26
// Gearbox Rated Output Torque: 29.1 N-m
// Gearbox Maximum Output Torque: 39.4 N-m
// Gearbox Efficiency: 94%
//
//                        6.36 A * 29.1 N-m
// Motor Rated Current = ------------------- = 2.127 A
//                       26 * 3.56 N-m * 94%
//
//                        6.36 A * 39.4 N-m
// Max Motor Current   = ------------------- = 2.880 A
//                       26 * 3.56 N-m * 94%

void user()
{
  // It is recommended to use CFG.txt for these object configurations.
 
  // Closed Loop Commissioning

  // Pole Pair Count = 50
  od_write(0x2030, 0x00, 50);

  // Max Motor Current = 2880 (mA)
  od_write(0x2031, 0x00, 2880);

  // Motor Rated Current = 2127 (mA)
  // "Nominal current" in Plug & Drive Studio 2.0.5
  // 6075 is mapped to 203B:01
  od_write(0x6075, 0x00, 2127);

  // Max Current = 1000 (tenths of a percent)
  od_write(0x6073, 0x00, 1000);

  // Maximum Duration of Peak Current = 100 (ms)
  od_write(0x203B, 0x02, 100);

  // Motor Drive Submode Select
  U32 object_3202h = 0;
  object_3202h |= (1 << 0); // CL/OL = 1 (closed-loop)
  od_write(0x3202, 0x00, object_3202h); 

  // Modes Of Operation = -1 (Clock-direction mode)
  od_write(0x6060, 0x00, -1);

  // Clock Direction Multiplier = 128
  od_write(0x2057, 0x00, 128);

  // Clock Direction Divider = 1
  od_write(0x2058, 0x00, 1);

  // CiA 402 Power State Machine

  // Wait for "Switch on disabled" state.
  /*
  do {
          yield();
   } while ((In.StatusWord & 0x4F) != 0x40);
  */

  // Transition 1 - "Shutdown"
  // "Switched on disabled" -> "Ready to switch on"
  Out.ControlWord = 0x6;
  // od_write(0x6040, 0x00, 0x6);

  // Wait for "Ready to switch on" state.
  do {
    yield();
  } while ((In.StatusWord & 0x6F) != 0x21);

  // Transition 2 - "Switch on"
  // "Ready to switch on" -> "Switched on"
  Out.ControlWord = 0x7;
  // od_write(0x6040, 0x00, 0x7);

  // Wait for "Switched on" state.
  do {
    yield();
  } while ((In.StatusWord & 0x6F) != 0x23);

  // Transition 3 - "Enable operation"
  // "Switched on" -> "Operation enabled"
  Out.ControlWord = 0xF;
  // od_write(0x6040, 0x00, 0xF);

  // Wait for "Operation enabled" state.
  do {
    yield();
  } while ((In.StatusWord & 0x6F) != 0x27);

  // Stop the NanoJ program.
  // NanoJ Control::ON = 0
  od_write(0x2300, 0x00, 0x0);
}
