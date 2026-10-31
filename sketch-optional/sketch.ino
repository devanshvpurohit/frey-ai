/**
 * ==============================================================================
 * FREY AI — Arduino UNO Q Real-Time Microcontroller Companion Sketch
 * Architecture: Arduino UNO Q (STM32 / Zephyr Core)
 *
 * Responsibilities:
 * 1. Hardware Heartbeat: Indicates real-time MCU vitality on LED_BUILTIN.
 * 2. Visual / Audio Disease Alert: Lights up alert indicator or triggers buzzer
 *    when the Qualcomm Linux processor identifies plant pathogens via YOLO11n.
 * 3. Physical Snapshot Trigger: Push-button on digital pin 2 signals the Linux
 *    pipeline to capture a high-resolution inspection frame.
 * ==============================================================================
 */

#include <Arduino.h>

// Hardware Pin Definitions
#define PIN_STATUS_LED        LED_BUILTIN  // Pin 13
#define PIN_ALERT_OUTPUT      7            // Digital output for optional buzzer or red alert LED
#define PIN_SNAPSHOT_BUTTON   2            // Active-LOW momentary push button (internal pullup)

// Disease status states (from Linux AI inference)
#define STATE_NO_CANOPY       0
#define STATE_HEALTHY         1
#define STATE_DISEASED        2

volatile int currentDiseaseState = STATE_NO_CANOPY;
unsigned long lastHeartbeatTime = 0;
unsigned long lastButtonCheckTime = 0;
bool lastButtonState = HIGH;

// Optional Arduino App Lab Bridge forward declaration
#if defined(ARDUINO_UNOR4_WIFI) || defined(ARDUINO_UNO_Q) || defined(__ZEPHYR__)
  // Forward declare bridge if available in core
  extern "C" {
    __attribute__((weak)) void bridgeNotify(const char* name, const char* payload);
  }
#endif

void setup() {
  Serial.begin(115200);

  // Configure hardware pins
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_ALERT_OUTPUT, OUTPUT);
  pinMode(PIN_SNAPSHOT_BUTTON, INPUT_PULLUP);

  digitalWrite(PIN_STATUS_LED, LOW);
  digitalWrite(PIN_ALERT_OUTPUT, LOW);

  Serial.println(F("=================================================="));
  Serial.println(F("   FREY AI — ARDUINO UNO Q MCU COMPANION CORE     "));
  Serial.println(F("=================================================="));
  Serial.println(F("Pin 13: Heartbeat & Status Indicator"));
  Serial.println(F("Pin 7:  Pathology Alert Relay / Buzzer Output"));
  Serial.println(F("Pin 2:  Physical Snapshot Button (Active LOW)"));
  Serial.println(F("=================================================="));
}

void loop() {
  unsigned long now = millis();

  // 1. Process Physical Push-Button Trigger (Debounced, 50ms)
  if (now - lastButtonCheckTime >= 50) {
    lastButtonCheckTime = now;
    bool reading = digitalRead(PIN_SNAPSHOT_BUTTON);

    // Falling edge: button pressed
    if (reading == LOW && lastButtonState == HIGH) {
      Serial.println(F("[MCU] Hardware snapshot button pressed! Signaling Linux AI..."));
      // Visual feedback: flash LED
      digitalWrite(PIN_STATUS_LED, HIGH);
      delay(80);
      digitalWrite(PIN_STATUS_LED, LOW);

      // Signal over serial or bridge
      Serial.println(F("CMD:SNAPSHOT"));
    }
    lastButtonState = reading;
  }

  // 2. Hardware Heartbeat & Visual Alert Pattern
  if (currentDiseaseState == STATE_DISEASED) {
    // Fast flash when disease detected (100ms cycle)
    if (now - lastHeartbeatTime >= 120) {
      lastHeartbeatTime = now;
      digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
      digitalWrite(PIN_ALERT_OUTPUT, HIGH);
    }
  } else if (currentDiseaseState == STATE_HEALTHY) {
    // Solid steady ON for healthy canopy verification
    digitalWrite(PIN_STATUS_LED, HIGH);
    digitalWrite(PIN_ALERT_OUTPUT, LOW);
  } else {
    // Gentle 1 Hz breathing heartbeat while scanning
    if (now - lastHeartbeatTime >= 500) {
      lastHeartbeatTime = now;
      digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
      digitalWrite(PIN_ALERT_OUTPUT, LOW);
    }
  }

  // 3. Serial command processor (for direct testing or bridge pipe)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "STATE:0") {
      currentDiseaseState = STATE_NO_CANOPY;
      Serial.println(F("[MCU] State updated: NO_CANOPY"));
    } else if (cmd == "STATE:1") {
      currentDiseaseState = STATE_HEALTHY;
      Serial.println(F("[MCU] State updated: HEALTHY CANOPY"));
    } else if (cmd == "STATE:2") {
      currentDiseaseState = STATE_DISEASED;
      Serial.println(F("[MCU] State updated: PATHOGEN LESION DETECTED"));
    }
  }
}
