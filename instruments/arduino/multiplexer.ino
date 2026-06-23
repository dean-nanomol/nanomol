#include <Wire.h>

#define MCP1 0x20 // expander 1 A0 A1 A2 -> GND 
#define MCP2 0x21 // expander 2 A0 -> 5V A1 A2 -> GND

#define IODIRA 0x00 // Input/Output for GPIOA
#define IODIRB 0x01 // Input/Output for GPIOB
#define GPIOA 0x12 // value on the port A high or low
#define GPIOB 0x13 // value on the port B high or low

// store the current relay states for each expander port, this allows multiple relays to stay on at the same time
byte mcp1A_state = 0x00;
byte mcp1B_state = 0x00;
byte mcp2A_state = 0x00;
byte mcp2B_state = 0x00;

void writeRegister(byte deviceAddress, byte reg, byte value){
  // deviceAddress: which expander, reg: which register, value: output state  
  Wire.beginTransmission(deviceAddress);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

void allOff(){
  // turn all ports off
  mcp1A_state = 0x00;
  mcp1B_state = 0x00;
  mcp2A_state = 0x00;
  mcp2B_state = 0x00;
  writeRegister(MCP1, GPIOA, mcp1A_state);
  writeRegister(MCP1, GPIOB, mcp1B_state);
  writeRegister(MCP2, GPIOA, mcp2A_state);
  writeRegister(MCP2, GPIOB, mcp2B_state);
}

void setComponentState(int componentNumber, bool state){ // state: true = ON, false = OFF
  if(componentNumber < 1 || componentNumber > 25){
    Serial.println("Invalid component number");
    return;
  }

  int index = componentNumber - 1; //components start at 1, but bits start at 0
  byte address; // expander
  byte port; // A or B
  byte bitNumber; // bit position inside the selected port
  byte* stateVariable; // points to the state variable of the selected port

  if(index < 13){ // expander 1
    address = MCP1;

    if(index < 8){ //port A
      port = GPIOA;
      bitNumber = index;
      stateVariable = &mcp1A_state;
    }
    else{ // port B
      port = GPIOB;
      bitNumber = index - 8; // 8: pins for port A
      stateVariable = &mcp1B_state;
    }
  }
  else{ // expander 2
    address = MCP2; 
    int index2 = index - 13; // 13:pins for expander 1

    if(index2 < 8){ // port A
      port = GPIOA;
      bitNumber = index2;
      stateVariable = &mcp2A_state;
    }
    else{ //port B
      port = GPIOB;
      bitNumber = index2 - 8;
      stateVariable = &mcp2B_state;
    }
  }

  if(state){ // true = ON
    *stateVariable = *stateVariable | (1 << bitNumber); // Set the selected bit to 1 without changing the other relay states
    Serial.print("Component ");
    Serial.print(componentNumber);
    Serial.println(" ON");
  }
  else{
    *stateVariable = *stateVariable & ~(1 << bitNumber); // Set the selected bit to 0 without changing the other relay states
    Serial.print("Component ");
    Serial.print(componentNumber);
    Serial.println(" OFF");
  }

  writeRegister(address, port, *stateVariable);
}

bool getComponentState(int componentNumber){
   if(componentNumber < 1 || componentNumber > 25){
    return false;
  }
  int index = componentNumber - 1;

  if(index < 13){
    if(index < 8){
      return bitRead(mcp1A_state, index);
    }
    else{
      return bitRead(mcp1B_state, index - 8);
    }
  }
  else{
    int index2 = index - 13;

    if(index2 < 8){
      return bitRead(mcp2A_state, index2);
    }
    else{
      return bitRead(mcp2B_state, index2 - 8);
    }
  }
}

void setup(){
  Wire.begin();
  Serial.begin(115200);
  delay(1000);
  // All ports are outputs
  writeRegister(MCP1, IODIRA, 0x00);
  writeRegister(MCP1, IODIRB, 0x00);
  writeRegister(MCP2, IODIRA, 0x00);
  writeRegister(MCP2, IODIRB, 0x00);

  allOff();
  Serial.println("System ready");
  Serial.println("Commands: on 1 to on 25, off 1 to off 25, off all, status");
}

void loop(){
  if(Serial.available() > 0){
    String command = Serial.readStringUntil('\n');
    command.trim();

    if(command == "off all"){
      allOff();
      Serial.println("All components are off");
    }
    else if(command.startsWith("on ")){
      int componentNumber = command.substring(3).toInt();
      setComponentState(componentNumber, true);
    }
    else if(command.startsWith("off ")){
      int componentNumber = command.substring(4).toInt();
      setComponentState(componentNumber, false);
    }
    else if(command == "status"){
      for(int componentNumber = 1; componentNumber <= 25; componentNumber++){
        Serial.print(getComponentState(componentNumber));

        if(componentNumber < 25){
          Serial.print(",");
        }
      }
      Serial.println();
    }
    else{
      Serial.println("Unknown command");
    }
  }
}

/*
Only 25 outputs are used and divided between 2 expanders:
- MCP1 address 0x20 gives components 1 to 13
- MCP2 address 0x21 gives components 14 to 25

Mapping:
- Components 1 to 8   -> MCP1 GPIOA GPA0 to GPA7
- Components 9 to 13  -> MCP1 GPIOB GPB0 to GPB4
- Components 14 to 21 -> MCP2 GPIOA GPA0 to GPA7
- Components 22 to 25 -> MCP2 GPIOB GPB0 to GPB3

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

*/