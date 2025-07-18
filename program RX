#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <LoRa.h>
//WiFi
const char* ssid = "admin";
const char* password = "admin";
//API
const char* serverName = "https://palmtracker-production.up.railway.app/kirim-data";
// LoRa pin
#define SCK 5
#define MISO 19
#define MOSI 27
#define SS 18
#define RST 14
#define DIO0 26

void setup() {
  Serial.begin(115200);
  // Init WiFi
  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan ke WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nTerhubung ke WiFi");
  // Init LoRa
  SPI.begin(SCK, MISO, MOSI, SS);
  LoRa.setPins(SS, RST, DIO0);
  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa RX GAGAL!");
    while (1);
  }
  Serial.println("LoRa RX Siap");
}

void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String received = "";
    while (LoRa.available()) {
      received += (char)LoRa.read();
    }
    Serial.print("Diterima: ");
    Serial.println(received);
    int device = 0;
    float suhu = 0, kelembapan = 0, ph = 0;
    int nitrogen = 0, fosfor = 0, kalium = 0, konduktivitas = 0;
    float latitude = 0.0, longitude = 0.0;
    if (received.startsWith("TX1")) {
      device = 1;
      sscanf(received.c_str(), "TX1 N:%d,P:%d,K:%d,PH:%f,TEMP:%f,HUM:%f,LAT:%f,LNG:%f",
             &nitrogen, &fosfor, &kalium, &ph, &suhu, &kelembapan, &latitude, &longitude);

    } else if (received.startsWith("TX2")) {
      device = 2;
      sscanf(received.c_str(), "TX2 TEMP:%f,HUM:%f,LAT:%f,LNG:%f",
             &suhu, &kelembapan, &latitude, &longitude);
    }
    if (device > 0 && WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");
      StaticJsonDocument<512> jsonDoc;
      jsonDoc["device"] = device;
      jsonDoc["suhu"] = suhu;
      jsonDoc["kelembapan"] = kelembapan;
      jsonDoc["ph"] = ph;
      jsonDoc["nitrogen"] = nitrogen;
      jsonDoc["kalium"] = kalium;
      jsonDoc["fosfor"] = fosfor;
      jsonDoc["konduktivitas"] = konduktivitas;
      jsonDoc["latitude"] = latitude;
      jsonDoc["longitude"] = longitude;
      String requestBody;
      serializeJson(jsonDoc, requestBody);
      int httpResponseCode = http.POST(requestBody);
      if (httpResponseCode > 0) {
        Serial.printf("Kirim ke server (Device %d) berhasil! Kode: %d\n", device, httpResponseCode);
        Serial.println("Response: " + http.getString());
      } else {
        Serial.printf("Gagal kirim data! Error: %s\n", http.errorToString(httpResponseCode).c_str());
      }
      http.end();
    }
    delay(5000); // jeda biar tidak terlalu padat kiriman
  }
}
