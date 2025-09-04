const int ntc_pin = A0;      // NTC pin
const float R1 = 10000.0;    // 10K resistor
const float BETA = 3435.0;   // Beta coefficient (check your NTC's datasheet)
const float T0 = 298.15;     // Reference temperature in Kelvin (25°C = 298.15K)
const float R0 = 10000.0;    // NTC resistance at 25°C

void setup() {
    Serial.begin(9600);
}

void loop() {
    float ain = analogRead(ntc_pin);
    float R2 = R1 * (1023.0 / ain - 1.0);

    // Beta equation for calculating temperature in Kelvin
    float temp_k = 1.0 / ( (1.0 / T0) + (log(R2 / R0) / BETA) );
    float temp_c = temp_k - 273.15; // Convert to Celsius

    Serial.println(temp_c); // Directly output Celsius for the Serial Plotter

    delay(500);
}