/*
Available commands:
  on         
  off         
  query_status 
*/

const int pinRelay = 8; // pin 8 of the arduino

bool new_command_is_ready = false;
bool new_query_command_is_ready = false;
const byte max_command_length = 40;

char input_character;
char end_marker = '\n';
char input_command[max_command_length]; // on off or status

void setup() {
  Serial.begin(115200);
  pinMode(pinRelay, OUTPUT);
  digitalWrite(pinRelay, LOW); // start at LOW

  Serial.println("System ready");
  Serial.println("Available commands: on, off, query_status");
}

void loop() {
  read_command();
  reply_to_query();

  if (new_command_is_ready) {

    if (strcmp(input_command, "on") == 0) {
      relay_on();
    }
    else if (strcmp(input_command, "off") == 0) {
      relay_off();
    }
    else if (!new_query_command_is_ready) {
      Serial.println("error: unknown command");
      Serial.println("Available commands: on, off, query_status");
    }

    new_command_is_ready = false;
    new_query_command_is_ready = false;
  }
}

void read_command() {
  static byte i = 0;
  while (Serial.available() > 0 && new_command_is_ready == false) {
    input_character = Serial.read();
    if (input_character != end_marker) {
      if (input_character != '\r') {
        input_command[i] = input_character;
        i++;
      }
    }
    else {
      input_command[i] = char(0);
      i = 0;
     // Serial.println(input_command);
      new_command_is_ready = true;
      if (strstr(input_command, "query") != NULL) {
        new_query_command_is_ready = true;
      }
    }
  }
}

void reply_to_query() {
  if (new_query_command_is_ready) {
    if (strstr(input_command, "query_status") != NULL) {
      if (digitalRead(pinRelay) == HIGH) {
        Serial.println("Relay is currently on");
      } else {
        Serial.println("Relay is currently off");
      }
    }
    new_query_command_is_ready = false;
  }
}

void relay_on() {
  digitalWrite(pinRelay, HIGH);
  Serial.println("Relay on");
}

void relay_off() {
  digitalWrite(pinRelay, LOW);
  Serial.println("Relay off");
}
