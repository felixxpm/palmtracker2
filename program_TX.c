#include <ModbusMaster.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <SPI.h>
#include <LoRa.h>
#include <HardwareSerial.h>

//RS485 Sensor NPK
#define RXD2 16
#define TXD2 17
#define RS485_DE 33
#define RS485_RE 32

//OLED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

//LoRa
#define SCK 18
#define MISO 19
#define MOSI 23
#define SS 14
#define RST 25
#define DIO0 26
#include <TinyGPSPlus.h>

//GPS
#define GPS_RX 13
#define GPS_TX 4
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);

//Modbus
ModbusMaster node;

//Tabel Kalibrasi Kelembapan
const float calTableKelembapan[][2] = {
  {28, 0}, {30, 10}, {37, 20}, {86, 30}, {153, 40},
  {405, 50}, {526, 60}, {625, 70}, {713, 80}, {799, 90}, {850, 100}
};
const int tableSizeKelembapan = sizeof(calTableKelembapan) / sizeof(calTableKelembapan[0]);

float kalibrasiKelembapan(float raw) {
  if (raw <= calTableKelembapan[0][0]) return calTableKelembapan[0][1];
  if (raw >= calTableKelembapan[tableSizeKelembapan - 1][0]) return calTableKelembapan[tableSizeKelembapan - 1][1];
  for (int i = 0; i < tableSizeKelembapan - 1; i++) {
    float x1 = calTableKelembapan[i][0], y1 = calTableKelembapan[i][1];
    float x2 = calTableKelembapan[i + 1][0], y2 = calTableKelembapan[i + 1][1];
    if (raw >= x1 && raw <= x2)
      return y1 + ((raw - x1) * (y2 - y1)) / (x2 - x1);
  }
  return raw;
}

//Kalibrasi NPK
const int calTableNitrogen[][2] = {
  {0, 0}, {3, 3}, {23, 8}, {44, 20}, {108, 40}, {144, 55}, {166, 62},
  {213, 94}, {214, 74}, {313, 94}, {336, 112}, {375, 112}, {420, 144},
  {483, 144}, {572, 165}, {600, 195}, {630, 235}
};
const int tableSizeNitrogen = sizeof(calTableNitrogen) / sizeof(calTableNitrogen[0]);

const int calTablePhosphor[][2] = {
  {0, 0}, {97, 10}, {216, 35}, {414, 70}, {558, 95}, {784, 124}, {917, 137},
  {1004, 150}, {1058, 158}, {1143, 164}, {1414, 195}, {1524, 237}, {1596, 273},
  {1637, 289}, {1754, 358}, {1800, 399}
};
const int tableSizePhosphor = sizeof(calTablePhosphor) / sizeof(calTablePhosphor[0]);

const int calTableKalium[][2] = {
  {0, 0}, {58, 13}, {100, 27}, {140, 61}, {257, 95}, {314, 120}, {428, 182},
  {487, 194}, {669, 245}, {763, 272}, {804, 288}, {916, 321}, {955, 338},
  {1017, 351}, {1118, 375}, {1245, 406}, {1444, 418}, {1504, 427}, {1555, 449}
};
const int tableSizeKalium = sizeof(calTableKalium) / sizeof(calTableKalium[0]);

int kalibrasi(int raw, const int table[][2], int size) {
  if (raw <= table[0][0]) return table[0][1];
  if (raw >= table[size - 1][0]) return table[size - 1][1];
  for (int i = 0; i < size - 1; i++) {
    if (raw >= table[i][0] && raw <= table[i + 1][0]) {
      int x1 = table[i][0], y1 = table[i][1];
      int x2 = table[i + 1][0], y2 = table[i + 1][1];
      return y1 + ((float)(raw - x1) * (y2 - y1)) / (x2 - x1);
    }
  }
  return 0;
}

void preTransmission() {
  digitalWrite(RS485_RE, HIGH);
  digitalWrite(RS485_DE, HIGH);
}

void postTransmission() {
  digitalWrite(RS485_DE, LOW);
  digitalWrite(RS485_RE, LOW);
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(4800, SERIAL_8N1, RXD2, TXD2);
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  pinMode(RS485_DE, OUTPUT);
  pinMode(RS485_RE, OUTPUT);
  digitalWrite(RS485_DE, LOW);
  digitalWrite(RS485_RE, LOW);

  node.begin(1, Serial2);
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);

  //OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED gagal");
    while (1);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("Inisialisasi...");
  display.display();

  //LoRa
  SPI.begin(SCK, MISO, MOSI, SS);
  LoRa.setPins(SS, RST, DIO0);
  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa gagal");
    display.println("LoRa Gagal!");
    display.display();
    while (1);
  }

  Serial.println("LoRa TX Siap");
  display.println("LoRa TX Siap");
  display.display();
}

void loop() {
  uint8_t result = node.readHoldingRegisters(0x0000, 7);

  if (result == node.ku8MBSuccess) {
    uint16_t data[7];
    for (int i = 0; i < 7; i++) {
      data[i] = node.getResponseBuffer(i);
    }
    //Update data GPS
    while (gpsSerial.available()) {
      gps.encode(gpsSerial.read());
    }

    //Ambil nilai GPS
    double latitude = gps.location.isValid() ? gps.location.lat() : 0.0;
    double longitude = gps.location.isValid() ? gps.location.lng() : 0.0;


    float kelembapanRaw = data[0];
    float kelembapan = kalibrasiKelembapan(kelembapanRaw);
    float temperature = data[1] / 10.0;
    float pH          = data[3] / 10.0;
    int nitrogen      = kalibrasi(data[4], calTableNitrogen, tableSizeNitrogen);
    int phosphor      = kalibrasi(data[5], calTablePhosphor, tableSizePhosphor);
    int kalium        = kalibrasi(data[6], calTableKalium, tableSizeKalium);

    //Format pesan
    String loraMsg = "TX1 N:" + String(nitrogen) +
                     ", P:" + String(phosphor) +
                     ", K:" + String(kalium) +
                     ", PH:" + String(pH, 1) +
                     ", TEMP:" + String(temperature, 1) +
                     ", HUM:" + String(kelembapan, 1) +
                     ", LAT:" + String(latitude, 6) +
                     ", LNG:" + String(longitude, 6);


    //Kirim LoRa
    LoRa.beginPacket();
    LoRa.print(loraMsg);
    LoRa.endPacket();

    //OLED tampilan
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("TX1 -> RX");
    display.setCursor(0, 16);
    display.printf("N:%d P:%d K:%d", nitrogen, phosphor, kalium);
    display.setCursor(0, 32);
    display.printf("PH:%.1f T:%.1f H:%.1f", pH, temperature, kelembapan);
    display.display();
    display.setCursor(0, 48);
    display.setTextSize(1);
    display.printf("LAT:%.2f", latitude);
    display.setCursor(64, 48);
    display.printf("LNG:%.2f", longitude);
    display.display();


    Serial.println("Kirim: " + loraMsg);
  } else {
    Serial.print("Gagal baca sensor. Error: ");
    Serial.println(result);
  }

  delay(5000);
}
