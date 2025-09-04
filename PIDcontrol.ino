#include <PID_v1.h> // Nur noch die PID-Bibliothek wird benötigt

// ================================================================
// 🔹 Konstanten und Pin-Definitionen
// ================================================================

// --- NTC-Widerstandsmessung ---
const int ntcPin = A0;            // Pin, an dem der NTC-Spannungsteiler hängt
const float R1 = 10000.0;         // Wert des Festwiderstands im Spannungsteiler (10k Ohm)
const float BETA = 3435.0;        // Beta-Koeffizient des Thermistors (aus Datenblatt!)
const float T0 = 298.15;          // Referenztemperatur in Kelvin (25°C = 298.15K)
const float R0 = 10000.0;         // Nennwiderstand des NTC bei Referenztemperatur T0 (10k Ohm)

// --- MOSFET PWM-Ausgang ---
const int mosfetPin = 9;          // PWM-Pin für das MOSFET Gate

// ================================================================
// 🔹 PID-Variablen
// ================================================================
double Setpoint = 37.0;           // Ziel-Temperatur in °C
double Input, Output;             // Variablen für den PID (Ist-Temperatur, Berechneter Output)

// *** PID Tuning Werte ***
// Ziel: Aggressivere Reaktion, schnelleres Absenken des PWM bei Überschreiten.
//       Akzeptieren, dass initial nicht sofort 255 PWM erreicht wird.

// Kp: Beeinflusst die Stärke der Reaktion auf den aktuellen Fehler.
//     Wird vorerst bei 10 belassen.
double Kp = 36.2768;

// Ki: Beeinflusst die Reaktion auf vergangene Fehler (eliminiert Steady-State Error).
//     Wird STARK reduziert, um "Integral Windup" zu verringern und
//     den PWM-Wert bei Überschreiten schneller sinken zu lassen.
double Ki = 0.1448; // <--- Deutlich reduziert von 0.5

// Kd: Beeinflusst die Reaktion auf die Änderungsrate des Fehlers (dämpft Schwingungen).
//     Wird leicht erhöht, um die Reaktion zu beschleunigen und
//     das Überschwingen trotz reduziertem Ki zu dämpfen.
double Kd = 0; // <--- Leicht erhöht von 20

// PID-Regler Instanz mit den neuen Werten
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);

// ================================================================
// 🔹 PWM-Begrenzung (Optional aber empfohlen)
// ================================================================
int finalPWM = 0;
const int maxPWM = 255; // Volle Leistung erlauben

// ================================================================
// 🔹 PID-Steuerung & Timing
// ================================================================
bool pidAktiv = true; // PID startet standardmäßig aktiv
unsigned long lastPlotterMillis = 0; // Für non-blocking Plotter-Ausgabe
const long plotterInterval = 1000;    // Sende Daten an Plotter jede Sekunde

// ================================================================
//                           SETUP
// ================================================================
void setup() {
  Serial.begin(9600);
  pinMode(mosfetPin, OUTPUT);
  digitalWrite(mosfetPin, LOW); // Sicherstellen, dass Heizung anfangs aus ist

  myPID.SetOutputLimits(0, maxPWM); // PWM Bereich für PID-Output begrenzen
  myPID.SetMode(AUTOMATIC);         // PID-Regler aktivieren

  // Ausgabe der verwendeten Einstellungen
  Serial.println(F("PID-Regler gestartet mit angepassten Werten."));
  Serial.print(F("Setpoint: ")); Serial.println(Setpoint);
  Serial.print(F("Kp: ")); Serial.println(Kp);
  Serial.print(F("Ki: ")); Serial.println(Ki); // Zeigt den neuen Wert an
  Serial.print(F("Kd: ")); Serial.println(Kd); // Zeigt den neuen Wert an
  Serial.print(F("Max PWM: ")); Serial.println(maxPWM);
}

// ================================================================
//                            LOOP
// ================================================================
void loop() {
  unsigned long currentMillis = millis(); // Aktuelle Zeit holen für Timing

  // --- 1. Serielle Eingaben prüfen (PID An/Aus) ---
  if (Serial.available() > 0) {
    char eingabe = Serial.read();
    if (eingabe == '0') {
      pidAktiv = false;
      myPID.SetMode(MANUAL);
      finalPWM = 0;
      analogWrite(mosfetPin, finalPWM);
      Serial.println(F("PID deaktiviert"));
    } else if (eingabe == '1') {
      pidAktiv = true;
      // WICHTIG: Internen Zustand des PID zurücksetzen, wenn er wieder aktiviert wird?
      // Die PID_v1 Bibliothek macht das i.d.R. automatisch beim Wechsel zu AUTOMATIC,
      // aber explizit kann es manchmal helfen, wenn unerwartetes Verhalten auftritt.
      // myPID.Initialize(); // Optional, falls nötig
      myPID.SetMode(AUTOMATIC);
      Serial.println(F("PID aktiviert"));
    }
  }

  // --- 2. Temperatur vom NTC berechnen ---
  Input = getTemperature(); // Liest die aktuelle Temperatur

  // --- 3. PID berechnen und PWM-Wert direkt setzen (wenn aktiv) ---
  if (pidAktiv) {
    // Die PID-Bibliothek berechnet den nötigen Output basierend auf Input, Setpoint und Kp, Ki, Kd
    bool computed = myPID.Compute(); // Compute gibt true zurück, wenn ein neuer Output berechnet wurde (abhängig vom Sample Time)

    // Prüfen ob Compute() einen neuen Wert geliefert hat (optional, aber gut zu wissen)
    if (computed) {
        // Begrenze den Output auf den erlaubten PWM-Bereich (sollte durch SetOutputLimits schon geschehen, aber doppelt hält besser)
        finalPWM = (int)constrain(Output, 0, maxPWM);
    }
    // Wenn nicht computed, behalte den alten finalPWM-Wert

  } else {
    // Falls PID deaktiviert ist, stelle sicher, dass PWM 0 ist
    finalPWM = 0;
  }

  // --- 4. Finalen PWM-Wert an MOSFET senden ---
  analogWrite(mosfetPin, finalPWM);

  // --- 5. Serielle Ausgabe für Plotter (non-blocking) ---
  if (currentMillis - lastPlotterMillis >= plotterInterval) {
    lastPlotterMillis = currentMillis; // Zeit für nächste Ausgabe merken

    Serial.print(Input, 2);      // Ist-Temperatur (mit 2 Nachkommastellen)
    Serial.print(",");
    Serial.print(Setpoint, 2);   // Soll-Temperatur (mit 2 Nachkommastellen)
    Serial.print(",");
    Serial.println(finalPWM);    // Tatsächlich gesendeter PWM-Wert
  }

  // KEIN delay() hier! Die Loop läuft so schnell wie möglich.
  // Die PID-Bibliothek kümmert sich intern um das richtige Timing (Sample Time).

} // Ende loop()

// ================================================================
// Funktion zur Temperaturberechnung aus dem NTC-Widerstand
// (Verwendet Beta-Formel der Steinhart-Hart Gleichung)
// ================================================================
double getTemperature() {
  // Optional: Mehrere Messungen mitteln für glatteres Signal
  int numReadings = 5;
  float totalAin = 0;
  for(int i=0; i<numReadings; i++) {
    totalAin += analogRead(ntcPin);
    delayMicroseconds(100); // Kleine Pause zwischen den Messungen
  }
  float ain = totalAin / numReadings;

  // Prüfe auf unsinnige ADC-Werte (Kurzschluss/Unterbrechung)
  if (ain < 5 || ain > 1018) {
     // Serial.println(F("WARNUNG: NTC ADC Wert nahe Limit!")); // Weniger gesprächig
     // Optional: Einen Fehlerwert zurückgeben oder letzte gültige Messung
  }

  // Vermeide Division durch Null oder negative Werte bei ain
  if (ain <= 0) ain = 1; // Setze auf Minimum, um Fehler zu vermeiden
  if (ain >= 1023) ain = 1022; // Setze auf Maximum

  // Berechne Widerstand R2
  float R2 = R1 * (1023.0 / ain - 1.0);

   // Prüfe auf unsinnigen Widerstandswert
   if (R2 <= 0) {
       // Serial.println(F("FEHLER: NTC Widerstandsberechnung ungültig!")); // Weniger gesprächig
       return -999.0; // Fehlercode zurückgeben
   }

  // Berechne Temperatur in Kelvin mittels Beta-Formel
  // log() ist der natürliche Logarithmus (ln)
  float temp_k = 1.0 / ( (1.0 / T0) + (log(R2 / R0) / BETA) );

  // Konvertiere Kelvin zu Celsius
  return (double)(temp_k - 273.15);
}