/*
Arduino controller for 25-pin relay multiplexer with 3 inputs and 12 + 12 + 1 outputs.
Each input connects to specific output pins according to the PCB layout:
COM_MEAS_1: pins 1 to 6, and 14 to 19
COM_MEAS_2: pins 8 to 13, and 20 to 25
COM_MEAS_3: pin 7

Available commands:

status?
  returns a string of 25 digits, each 0 or 1, indicating state of each pin 1 ... 25

on P
  P : int
    pin number
  turn on (close) relay connected to pin P

off P
  P : int
    pin number
  turn off (open) relay connected to pin P

off all
  turn off all pins
  
*/

#include <Wire.h>
#include <string.h>
#include <stdlib.h>

#define MCP1 0x20 // expander 1: A0 A1 A2 -> GND 
#define MCP2 0x21 // expander 2: A0 -> 5V , A1 A2 -> GND
#define MCP_CONTROL_PIN 2

#define IODIRA 0x00 // Input/Output for GPIOA
#define IODIRB 0x01 // Input/Output for GPIOB
#define GPIOA 0x12 // value on the port A high or low
#define GPIOB 0x13 // value on the port B high or low
#define OLATA 0x14 // output latch register for port A
#define OLATB 0x15 // output latch register for port B

// Each relay on the multiplexer PCB is controlled by a pin on one of the port expanders.
// Each expander has two ports, A and B, with 8 pins each.
// Each pin is identified by its device address (expander 1 or 2), its port on that expander (GPIOA or GPIOB),
// and its bit number on that port (0 to 7).
// The state of each port is read/written as a byte (8 bits), where each bit is 0 or 1 if the pin is set LOW or HIGH.

// Define arrays to map each pin index (= pin number -1) to its corresponding expander address, port, and bit number.
byte index_map[] = {    // for positional index reference only, not used
  0,     1,     2,     3,     4,     5,     6,     7,     8,     9,     10,    11,    12,
  13,    14,    15,    16,    17,    18,    19,    20,    21,    22,    23,    24
};
byte address_map[] = {
  MCP1,  MCP1,  MCP1,  MCP1,  MCP1,  MCP1,  MCP1,  MCP2,  MCP2,  MCP2,  MCP2,  MCP2,  MCP2,
  MCP1,  MCP1,  MCP1,  MCP1,  MCP1,  MCP1,  MCP2,  MCP2,  MCP2,  MCP2,  MCP2,  MCP2
};
byte port_map[] = {
  GPIOA, GPIOB, GPIOA, GPIOA, GPIOB, GPIOB, GPIOB, GPIOB, GPIOB, GPIOA, GPIOA, GPIOB, GPIOA,
  GPIOA, GPIOA, GPIOA, GPIOA, GPIOA, GPIOB, GPIOA, GPIOA, GPIOA, GPIOA, GPIOB, GPIOA
};
byte bitNumber_map[] = {
  1,     2,     6,     2,     4,     3,     1,     3,     2,     6,     0,     1,     5,
  4,     7,     0,     3,     5,     0,     3,     7,     2,     4,     0,     1
};

byte index; // to store pin index when writing/reading pin state
byte regState; // to store the register state of a selected port

// variables for serial communication
bool new_command_is_ready = false;
bool new_query_command_is_ready = false;
const byte max_command_length = 40;
char input_character;
char end_marker = '\n';
char input_command[max_command_length];

void writeRegister(byte deviceAddress, byte port, byte value){
  // deviceAddress: which expander, port: which register, value: output state
  Wire.beginTransmission(deviceAddress);
  Wire.write(port);
  Wire.write(value);
  Wire.endTransmission();
}

byte readRegister(byte deviceAddress, byte port){
  // deviceAddress: which expander, port: which register
    Wire.beginTransmission(deviceAddress);
    Wire.write(port);
    Wire.endTransmission(false);
    Wire.requestFrom((byte)deviceAddress, (size_t)1);
    if (Wire.available()) {
        return Wire.read();
    }
    return 0;
}

void offAll(){
  // turn all ports off
  writeRegister(MCP1, GPIOA, 0x00);
  writeRegister(MCP1, GPIOB, 0x00);
  writeRegister(MCP2, GPIOA, 0x00);
  writeRegister(MCP2, GPIOB, 0x00);
}

void setPinState(byte pinNumber, bool state){ // state: true = ON, false = OFF
  if(pinNumber < 1 || pinNumber > 25){
    Serial.println("Invalid pin number");
    return;
  }
  index = pinNumber - 1; // pins start at 1, but bits start at 0
  regState = readRegister(address_map[index], port_map[index]);
  if(state){ // true = ON
    regState |= (1 << bitNumber_map[index]); // Set the selected bit to 1 without changing the other relay states
  }
  else{
    regState &= ~(1 << bitNumber_map[index]); // Set the selected bit to 0 without changing the other relay states
  }
  writeRegister(address_map[index], port_map[index], regState);
}

bool getPinState(byte pinNumber){
  index = pinNumber - 1;
  regState = readRegister(address_map[index], port_map[index]);
  return bitRead(regState, bitNumber_map[index]);
}

void setup(){
  Serial.begin(115200);

  pinMode(MCP_CONTROL_PIN, OUTPUT);
  digitalWrite(MCP_CONTROL_PIN, LOW);
  delay(10);
  digitalWrite(MCP_CONTROL_PIN, HIGH);
  delay(10);

  Wire.begin();
  delay(50);

  // all outputs LOW
  writeRegister(MCP1, OLATA, 0x00);
  writeRegister(MCP1, OLATB, 0x00);
  writeRegister(MCP2, OLATA, 0x00);
  writeRegister(MCP2, OLATB, 0x00);

  // all ports are outputs
  writeRegister(MCP1, IODIRA, 0x00);
  writeRegister(MCP1, IODIRB, 0x00);
  writeRegister(MCP2, IODIRA, 0x00);
  writeRegister(MCP2, IODIRB, 0x00);

  offAll();
}

void loop(){
  read_command();
  reply_to_query();

  if(new_command_is_ready){
    if(strcmp(input_command, "off all") == 0){
      offAll();
    }
    else if(strncmp(input_command, "on ", 3) == 0){
      int pinNumber = atoi(input_command + 3);
      setPinState(pinNumber, true);
    }
    else if(strncmp(input_command, "off ", 4) == 0){
      int pinNumber = atoi(input_command + 4);
      setPinState(pinNumber, false);
    }
    new_command_is_ready = false;
  }
}

void read_command(){
  // build up command string until reaching end_marker character
  static byte i = 0;

  // read serial input
  while(Serial.available() > 0 && new_command_is_ready == false){
    // read the incoming string
    input_character = Serial.read();
    if(input_character != end_marker){
      if(i < max_command_length - 1){
        input_command[i] = input_character;
        i++;
      }
    }
    else{
      // end_marker received, terminate command string with null character
      input_command[i] = char(0);
      i = 0;

      // identify command type
      if(strcmp(input_command, "status?") == 0){
        new_query_command_is_ready = true;
      }
      else {
        new_command_is_ready = true;
      }
    }
  }
}

void reply_to_query(){
  if(new_query_command_is_ready){
    if(strcmp(input_command, "status?") == 0){
      for(byte pinNumber = 1; pinNumber <= 25; pinNumber++){
        Serial.print(getPinState(pinNumber));
      }
      Serial.println();
    }
    new_query_command_is_ready = false;
  }
}

/*
Only 25 outputs are used and divided between 2 expanders:
- MCP1 address 0x20 gives pins 1 to 7 and 14 to 19
- MCP2 address 0x21 gives pins 8 to 13 and 20 to 25

Mapping:
pin 1 -> index 0 -> MCP1 GPA1
pin 2 -> index 1 -> MCP1 GPB2
pin 3 -> index 2 -> MCP1 GPA6
pin 4 -> index 3 -> MCP1 GPA2
pin 5 -> index 4 -> MCP1 GPB4
pin 6 -> index 5 -> MCP1 GPB3
pin 7 -> index 6 -> MCP1 GPB1
pin 8 -> index 7 -> MCP2 GPB3
pin 9 -> index 8 -> MCP2 GPB2
pin 10 -> index 9 -> MCP2 GPA6
pin 11 -> index 10 -> MCP2 GPA0
pin 12 -> index 11 -> MCP2 GPB1
pin 13 -> index 12 -> MCP2 GPA5
pin 14 -> index 13 -> MCP1 GPA4
pin 15 -> index 14 -> MCP1 GPA7
pin 16 -> index 15 -> MCP1 GPA0
pin 17 -> index 16 -> MCP1 GPA3
pin 18 -> index 17 -> MCP1 GPA5
pin 19 -> index 18 -> MCP1 GPB0
pin 20 -> index 19 -> MCP2 GPA3
pin 21 -> index 20 -> MCP2 GPA7
pin 22 -> index 21 -> MCP2 GPA2
pin 23 -> index 22 -> MCP2 GPA4
pin 24 -> index 23 -> MCP2 GPB0
pin 25 -> index 24 -> MCP2 GPA1

The address of each expander is chosen with pins A0, A1, A2:

A2 A1 A0 = 0 0 0 -> address 0x20
A2 A1 A0 = 0 0 1 -> address 0x21
A2 A1 A0 = 0 1 0 -> address 0x22
A2 A1 A0 = 0 1 1 -> address 0x23
A2 A1 A0 = 1 0 0 -> address 0x24
A2 A1 A0 = 1 0 1 -> address 0x25
A2 A1 A0 = 1 1 0 -> address 0x26
A2 A1 A0 = 1 1 1 -> address 0x27

To find the address:
GND = 0 and 5V = 1

address = 0x20 + A0 + 2*A1 + 4*A2

Example:
For 0x25:
0x25 = 0x20 + 5
5 = 4 + 1
So A2 and A0 are connected to 5V, and A1 is connected to GND.
*/
