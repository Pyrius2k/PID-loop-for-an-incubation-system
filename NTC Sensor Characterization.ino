#include <PID_v1.h> // Only the PID library is needed

// ================================================================
// 🔹 Constants and Pin Definitions
// ================================================================

// --- NTC Resistor Measurement ---
const int ntcPin = A0;      // Pin where the NTC voltage divider is connected
const float R1 = 10000.0;   // Value of the fixed resistor in the voltage divider (10k Ohm)
const float BETA = 3435.0;  // Beta coefficient of the thermistor (from datasheet!)
const float T0 = 298.15;    // Reference temperature in Kelvin (25°C = 298.15K)
const float R0 = 10000.0;   // Nominal resistance of the NTC at reference temperature T0 (10k Ohm)

// --- MOSFET PWM Output ---
const int mosfetPin = 9;    // PWM pin for the MOSFET gate

// ================================================================
// 🔹 PID Variables
// ================================================================
double Setpoint = 37.0;     // Target temperature in °C (relevant for PID mode and plotter)
double Input, Output;       // Variables for the PID (Current temperature, Calculated output)

// *** PID Tuning Values ***
double Kp = 10;
double Ki = 0.15;
double Kd = 25;

// PID controller instance
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);

// ================================================================
// 🔹 PWM Limiting & Manual Control
// ================================================================
int finalPWM = 0;
const int maxPWM = 255;
int manualPWM = 0; // Stores the manually set PWM value

// ================================================================
// 🔹 Control Modes
// ================================================================
#define MODE_OFF 0
#define MODE_PID 1
#define MODE_MANUAL 2
int controlMode = MODE_OFF; // Starts in OFF mode

// ================================================================
// 🔹 Timing
// ================================================================
unsigned long lastPlotterMillis = 0; // For non-blocking plotter output
const long plotterInterval = 1000;    // Send data to plotter every second

// ================================================================
//                         SETUP
// ================================================================
void setup() {
  Serial.begin(9600);
  pinMode(mosfetPin, OUTPUT);
  digitalWrite(mosfetPin, LOW); // Ensure heating is off initially

  myPID.SetOutputLimits(0, maxPWM); // Limit PWM range for PID output

  // --- Set initial mode ---
  if (controlMode == MODE_PID) {
      myPID.SetMode(AUTOMATIC);
      // This message is not output at startup since controlMode = MODE_OFF
      Serial.println(F("System starts in PID mode."));
  } else if (controlMode == MODE_MANUAL) {
      myPID.SetMode(MANUAL);
      finalPWM = manualPWM;
      // This message is not output at startup
      Serial.print(F("System starts in MANUAL mode with PWM: "));
      Serial.println(finalPWM);
  } else { // MODE_OFF - This block is now executed
      myPID.SetMode(MANUAL); // Turn off PID calculations
      finalPWM = 0;           // Ensure PWM is 0
      Serial.println(F("System starts in OFF mode (PWM=0)."));
      Serial.println(F("Send 'm' followed by 0-255 to heat manually."));
      // Here is the corrected output for the PID start command
      Serial.print(F("Send '1' to activate PID (Target: "));
      Serial.print(Setpoint, 1); // Serial.print can format float
      Serial.println(F("C)."));
  }

  // Output PID settings (relevant when PID is used)
  Serial.println(F("--- PID Parameters (if activated) ---"));
  Serial.print(F("Setpoint: ")); Serial.println(Setpoint);
  Serial.print(F("Kp: ")); Serial.println(Kp);
  Serial.print(F("Ki: ")); Serial.println(Ki);
  Serial.print(F("Kd: ")); Serial.println(Kd);
  Serial.print(F("Max PWM: ")); Serial.println(maxPWM);
  Serial.println(F("--- Control Commands ---"));
  Serial.println(F(" '0': Heater OFF"));
  Serial.println(F(" '1': PID Automatic ON"));
  Serial.println(F(" 'm': Manual PWM mode (then send a number 0-255)"));
  Serial.println(F("-------------------------"));
}

// ================================================================
//                           LOOP
// ================================================================
void loop() {
  unsigned long currentMillis = millis(); // Get current time for timing

  // --- 1. Calculate temperature from NTC ---
  Input = getTemperature(); // Read the current temperature (always read for monitoring)

  // --- 2. Check for serial input ---
  if (Serial.available() > 0) {
    char input = Serial.read();

    if (input == '0') { // OFF mode
      if (controlMode != MODE_OFF) {
        Serial.println(F("MODE: OFF (PWM=0)"));
      }
      controlMode = MODE_OFF;
      myPID.SetMode(MANUAL);
      finalPWM = 0;
      manualPWM = 0;
      analogWrite(mosfetPin, finalPWM);

    } else if (input == '1') { // PID mode
      if (controlMode != MODE_PID) {
        controlMode = MODE_PID;
        // myPID.Initialize(); // Optional
        myPID.SetMode(AUTOMATIC);
        // Here is the corrected output for the PID start
        Serial.print(F("MODE: PID Automatic ACTIVATED (Target: "));
        Serial.print(Setpoint, 1);
        Serial.println(F("C)"));
      } else {
        Serial.println(F("MODE: PID was already active."));
      }

    } else if (input == 'm' || input == 'M') { // Manual mode
       controlMode = MODE_MANUAL;
       myPID.SetMode(MANUAL);
       Serial.println(F("MODE: MANUAL. Please send a PWM value (0-255):"));
       long startTime = millis();
       while (Serial.available() == 0 && millis() - startTime < 5000) {
         delay(10);
       }
       if (Serial.available() > 0) {
          manualPWM = Serial.parseInt();
          manualPWM = constrain(manualPWM, 0, maxPWM);
          finalPWM = manualPWM;
          analogWrite(mosfetPin, finalPWM);
          Serial.print(F("Manual PWM set to: "));
          Serial.println(finalPWM);
       } else {
          // Here is the corrected output for the timeout
          Serial.print(F("Timeout - no PWM number received. PWM remains unchanged (current: "));
          Serial.print(finalPWM);
          Serial.println(F(")."));
       }
       while(Serial.available() > 0) { Serial.read(); }

    } else {
        // Ignore invalid input
    }
  } // End Serial.available()

  // --- 3. Determine and set PWM value based on mode ---
  if (controlMode == MODE_PID) {
    bool computed = myPID.Compute();
    if (computed) {
      finalPWM = (int)constrain(Output, 0, maxPWM);
      analogWrite(mosfetPin, finalPWM);
    }
  } else if (controlMode == MODE_MANUAL) {
    finalPWM = manualPWM;
    analogWrite(mosfetPin, finalPWM);
  } else { // MODE_OFF
    finalPWM = 0;
    analogWrite(mosfetPin, finalPWM);
  }


  // ================================================================
  // <---- HERE IS THE ADAPTED SECTION FOR THE PLOTTER ---->
  // --- 4. Serial output for plotter (non-blocking) ---
  // ================================================================
  if (currentMillis - lastPlotterMillis >= plotterInterval) {
    lastPlotterMillis = currentMillis; // Remember time for next output

    // Send the values for the plotter, ALWAYS in this order:
    // 1. Current temperature (Input)
    // 2. Target temperature (Setpoint) - Appears as a constant line at 37
    // 3. PWM value (finalPWM)

    Serial.print(Input, 2);      // Value 1: Current temperature
    Serial.print(",");           // Separator
    Serial.print(Setpoint, 2);   // Value 2: Target temperature (always send!) <--- Change here
    Serial.print(",");           // Separator
    Serial.println(finalPWM);    // Value 3: Current PWM value (ends the line)
  }
  // <---- END OF PLOTTER SECTION ---->


  // NO delay() here! The loop runs as fast as possible.

} // End loop()

// ================================================================
// Function to calculate temperature from the NTC resistance
// (Uses Beta formula of the Steinhart-Hart equation)
// ================================================================
double getTemperature() {
  // Optional: Average multiple measurements for a smoother signal
  int numReadings = 5;
  float totalAin = 0;
  for(int i=0; i<numReadings; i++) {
    totalAin += analogRead(ntcPin);
    delayMicroseconds(100); // Small pause between measurements
  }
  float ain = totalAin / numReadings;

  // Check for nonsensical ADC values (short circuit/break)
  if (ain < 5 || ain > 1018) {
      // Serial.println(F("WARNING: NTC ADC value near limit!")); // Less verbose
  }

  // Avoid division by zero or negative values for ain
  if (ain <= 0) ain = 1; // Set to minimum to avoid errors
  if (ain >= 1023) ain = 1022; // Set to maximum

  // Calculate resistance R2
  float R2 = R1 * (1023.0 / ain - 1.0);

    // Check for nonsensical resistance value
    if (R2 <= 0) {
        // Serial.println(F("ERROR: NTC resistance calculation invalid!")); // Less verbose
        return -999.0; // Return error code
    }

  // Calculate temperature in Kelvin using the Beta formula
  // log() is the natural logarithm (ln)
  float temp_k = 1.0 / ( (1.0 / T0) + (log(R2 / R0) / BETA) );

  // Convert Kelvin to Celsius
  return (double)(temp_k - 273.15);
}