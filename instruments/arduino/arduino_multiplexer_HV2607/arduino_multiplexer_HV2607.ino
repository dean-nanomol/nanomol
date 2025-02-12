#include <SPI.h>

#define CS 10

uint16_t num = 1;

//val16 = 

void setup() {
  //Serial.begin(9600);
  //Serial.println(num, BIN);
  //Serial.println(num);
  SPI.begin();
}

void loop() {
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE1));
  digitalWrite(CS, HIGH);
  SPI.transfer(B11111111);
  SPI.transfer(B11111111);
  digitalWrite(CS, LOW);
  delay(10);
  digitalWrite(CS, HIGH);
  delay(20000);

  digitalWrite(CS, HIGH);
  SPI.transfer(B00000000);
  SPI.transfer(B00000000);
  digitalWrite(CS, LOW);
  delay(10);
  digitalWrite(CS, HIGH);
  delay(20000);

  SPI.endTransaction();
}
