
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==========================================
// 1. CONFIGURATION WIFI
// ==========================================

// Remplacer par les identifiants du Wi-Fi
// utilise par ton ordinateur.
const char* WIFI_SSID = "NOM_WIFI";
const char* WIFI_PASSWORD = "MOT_DE_PASSE_WIFI";

// Adresse IPv4 de ton ordinateur
const char* SERVER_URL = "http://10.233.55.81:5000";

// ==========================================
// 2. BROCHES L298N (PROVISOIRES)
// ==========================================

const int ENA = 25;
const int IN1 = 26;
const int IN2 = 27;

const int ENB = 14;
const int IN3 = 18;
const int IN4 = 19;

// ==========================================
// 3. PARAMETRES
// ==========================================

const int MAX_SPEED = 255;

const unsigned long REQUEST_INTERVAL = 300;
const unsigned long CONNECTION_TIMEOUT = 2000;
const unsigned long WIFI_RETRY_INTERVAL = 5000;

unsigned long lastRequest = 0;
unsigned long lastCommunication = 0;
unsigned long lastWiFiAttempt = 0;

bool communicationActive = false;

// ==========================================
// 4. INITIALISATION DES MOTEURS
// ==========================================

void setupMotors() {

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();
}

// ==========================================
// 5. ARRET DES MOTEURS
// ==========================================

void stopMotors() {

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}

// ==========================================
// 6. AVANCER
// ==========================================

void moveForward(int speed) {

  speed = constrain(speed, 0, MAX_SPEED);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, speed);
  analogWrite(ENB, speed);
}

// ==========================================
// 7. RECULER
// ==========================================

void moveBackward(int speed) {

  speed = constrain(speed, 0, MAX_SPEED);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, speed);
  analogWrite(ENB, speed);
}

// ==========================================
// 8. TOURNER A GAUCHE
// ==========================================

void turnLeft(int speed) {

  speed = constrain(speed, 0, MAX_SPEED);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, speed);
  analogWrite(ENB, speed);
}

// ==========================================
// 9. TOURNER A DROITE
// ==========================================

void turnRight(int speed) {

  speed = constrain(speed, 0, MAX_SPEED);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, speed);
  analogWrite(ENB, speed);
}

// ==========================================
// 10. EXECUTION DES COMMANDES
// ==========================================

void executeCommand(String action, int speed) {

  speed = constrain(speed, 0, MAX_SPEED);

  if (action == "ARRET") {

    stopMotors();
  }

  else if (action == "AVANCER") {

    moveForward(speed);
  }

  else if (action == "RECULER") {

    moveBackward(speed);
  }

  else if (action == "TOURNER_GAUCHE") {

    turnLeft(speed);
  }

  else if (action == "TOURNER_DROITE") {

    turnRight(speed);
  }

  else if (action == "RALENTIR") {

    moveForward(speed);
  }

  else {

    stopMotors();
  }
}

// ==========================================
// 11. CONNEXION WIFI
// ==========================================

void connectWiFi() {

  Serial.println();
  Serial.println("Connexion au Wi-Fi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - start < 15000) {

    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println();
    Serial.println("Wi-Fi connecte !");

    Serial.print("Adresse IP ESP32 : ");
    Serial.println(WiFi.localIP());

    lastCommunication = millis();
    communicationActive = false;
  }

  else {

    Serial.println();
    Serial.println("Connexion Wi-Fi impossible.");

    stopMotors();
    communicationActive = false;
  }
}

// ==========================================
// 12. RECEPTION DES COMMANDES FLASK
// ==========================================

void receiveCommand() {

  if (WiFi.status() != WL_CONNECTED) {

    stopMotors();
    communicationActive = false;
    return;
  }

  HTTPClient http;

  String url = String(SERVER_URL) + "/api/esp32/command";

  http.begin(url);
  http.setTimeout(1000);

  int responseCode = http.GET();

  if (responseCode == HTTP_CODE_OK) {

    String payload = http.getString();

    JsonDocument doc;

    DeserializationError error =
        deserializeJson(doc, payload);

    if (!error && doc["command"].is<JsonObject>()) {

      String action = doc["command"]["action"] | "ARRET";

      int speed = doc["command"]["speed"] | 0;

      lastCommunication = millis();
      communicationActive = true;

      executeCommand(action, speed);

      Serial.print("Commande recue : ");
      Serial.println(action);

      Serial.print("Vitesse : ");
      Serial.println(speed);
    }

    else {

      stopMotors();
      communicationActive = false;

      Serial.println("Erreur : JSON invalide.");
    }
  }

  else {

    stopMotors();
    communicationActive = false;

    Serial.print("Erreur HTTP : ");
    Serial.println(responseCode);
  }

  http.end();
}

// ==========================================
// 13. INITIALISATION
// ==========================================

void setup() {

  Serial.begin(115200);

  setupMotors();

  Serial.println();
  Serial.println("================================");
  Serial.println("       ORION-ROVER");
  Serial.println("================================");

  connectWiFi();

  Serial.println("Initialisation terminee.");
}

// ==========================================
// 14. BOUCLE PRINCIPALE
// ==========================================

void loop() {

  // Vérification du Wi-Fi
  if (WiFi.status() != WL_CONNECTED) {

    stopMotors();
    communicationActive = false;

    if (millis() - lastWiFiAttempt >= WIFI_RETRY_INTERVAL) {

      lastWiFiAttempt = millis();
      connectWiFi();
    }

    delay(100);
    return;
  }

  // Récupération périodique des commandes
  if (millis() - lastRequest >= REQUEST_INTERVAL) {

    lastRequest = millis();

    receiveCommand();
  }

  // Arrêt si Flask ne répond plus
  if (millis() - lastCommunication > CONNECTION_TIMEOUT) {

    stopMotors();
    communicationActive = false;
  }
}
