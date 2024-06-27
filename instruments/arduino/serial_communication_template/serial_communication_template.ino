/*
Available commands:
[describe available commands here]
*/

bool new_command_is_ready = false;
bool new_query_command_is_ready = false;
const byte max_command_length = 40;
// variables for serial readout
char input_character;
char end_marker = '\n';
char input_command[max_command_length];

void setup() {
  Serial.begin(115200);
}

void loop() {
  read_command();
  reply_to_query();
  if (new_command_is_ready) {
    // identify command and react
    // command code and function calls go here ...
    if (strcmp(input_command, "do_something_command") == 0) {
      do_something()
    }

  // clear any unused commands, e.g. unrecognised commands
    new_command_is_ready = false;
    new_query_command_is_ready = false;
  }
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
      Serial.println(input_command);
      // identify command type
      new_command_is_ready = true;
      if (strstr(input_command, "query") != NULL) {
        new_query_command_is_ready = true;
      }
    }
  }
}

void reply_to_query() {
  if (new_query_command_is_ready) {
    if (strstr(input_command, "query_command") != NULL) {
      // reply to query goes here ...
      // Serial.println(...);
      ;
    }
  new_query_command_is_ready = false;
  }
}

void do_something() {
  // function code here
  ;
}
