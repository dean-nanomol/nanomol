/*
Arduino controller for solenoid actuated shutters.
Assign a digital pin to each shutter to control corresponding MOSFET gate.

Available commands:

status?
    returns state of shutters, 0: closed, 1: open

open,P
  P : int
    shutter (digital pin) number
  opens shutter connected to pin P

close,P
  P : int
    shutter (digital pin) number
  close shutter connected to pin P
*/

bool new_command_is_ready = false;
const byte max_command_length = 40;
// variables for serial readout
char input_character;
char end_marker = '\n';
char input_command[max_command_length];

// variables for command parsing
char command_type[max_command_length];
char shutter_index[5];

// shutter pin assignment
const byte shutter_635nm_pin = 2;
byte selected_shutter = shutter_635nm_pin;

void setup() {
  Serial.begin(115200);
  pinMode(shutter_635nm_pin, OUTPUT);
}

void loop() {
  read_command();
  if (new_command_is_ready) {
      // identify command and react
      if (strcmp(input_command, "status?") == 0) {
        // return state of selected shutter
        Serial.println(digitalRead(selected_shutter));
      }
      else {
        parse_command();
        if (strcmp(command_type, "open") == 0) {
          open_shutter(selected_shutter);
        }
        else if (strcmp(command_type, "close") == 0) {
          close_shutter(selected_shutter);
        }
      }
  } 
  // clear any unused commands, e.g. unrecognised commands
    new_command_is_ready = false;
}

void read_command() {
  // build up command string until reaching end_marker character
  static byte i = 0;
  // read serial input
  while (Serial.available() > 0
         && new_command_is_ready == false) {
    // read the incoming string
    input_character = Serial.read();
    if (input_character != end_marker) {
      input_command[i] = input_character;
      i++;
    }
    else {
      // end_marker received, terminate command string with null character
      input_command[i] = char(0);
      i = 0;
      // identify command type
      new_command_is_ready = true;
    }
  }
}

void parse_command() {
  // parse input_command for command type followed by selected shutter, separated by delimiter ","
  char * strtok_index;  // strtok returns pointer to first substring before delimiter ","
  strtok_index = strtok(input_command, ",");
  strcpy(command_type, strtok_index);
  strtok_index = strtok(NULL, ",");
  selected_shutter = atoi(strtok_index);
}

void open_shutter(byte shutter_pin) {
  digitalWrite(shutter_pin, HIGH);
}

void close_shutter(byte shutter_pin) {
  digitalWrite(shutter_pin, LOW);
}
