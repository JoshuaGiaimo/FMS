#include <WiFi.h>
#include <WiFiUdp.h>

// ================= WIFI SETTINGS =================
const char* WIFI_SSID = "KART_NET";
const char* WIFI_PASS = "12736EM1";

// -------- STATIC IP (LOCKED) --------
IPAddress local_IP(192, 168, 137, 207);
IPAddress gateway(192, 168, 137, 1);
IPAddress subnet(255, 255, 255, 0);

// ================= UDP =================
const int UDP_PORT = 4210;
const int ROBOT_ID = 1;
WiFiUDP udp;

// ================= OUTPUT =================
const int X_PIN = 23;   // HIGH while X is held

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("================================");
  Serial.println("ESP32 STATIC IP BUTTON TEST");
  Serial.println("================================");

  pinMode(X_PIN, OUTPUT);
  digitalWrite(X_PIN, LOW);

  Serial.print("Setting static IP: ");
  Serial.println(local_IP);

  WiFi.mode(WIFI_STA);

  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("❌ STATIC IP CONFIG FAILED");
  } else {
    Serial.println("✅ STATIC IP CONFIG OK");
  }

  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("✅ WIFI CONNECTED");
  Serial.print("IP ADDRESS: ");
  Serial.println(WiFi.localIP());

  udp.begin(UDP_PORT);
  Serial.print("UDP LISTENING ON PORT ");
  Serial.println(UDP_PORT);

  Serial.println("================================");
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    Serial.println();
    Serial.println("📨 UDP PACKET RECEIVED");

    char buf[64];
    int len = udp.read(buf, sizeof(buf) - 1);
    if (len > 0) buf[len] = '\0';

    Serial.print("RAW DATA: ");
    Serial.println(buf);

    int rid = 0;
    int buttons = 0;

    if (sscanf(buf, "%d,%d", &rid, &buttons) == 2) {
      Serial.print("PARSED → RobotID=");
      Serial.print(rid);
      Serial.print(" Buttons=");
      Serial.println(buttons);

      if (rid == ROBOT_ID) {
        bool xHeld = buttons & 1;

        digitalWrite(X_PIN, xHeld ? HIGH : LOW);

        Serial.print("X BUTTON: ");
        Serial.println(xHeld ? "HELD" : "RELEASED");

        Serial.print("GPIO 23 STATE: ");
        Serial.println(xHeld ? "HIGH" : "LOW");
      } else {
        Serial.println("⚠️ Robot ID MISMATCH");
      }
    } else {
      Serial.println("❌ PACKET PARSE FAILED");
    }

    Serial.println("--------------------------------");
  }
}
