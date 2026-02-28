#include <FastLED.h>

#define LED_PIN 23
#define NUM_LEDS 80

CRGB leds[NUM_LEDS];

void setup() {
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(12); // Reduce brightness to 10% (255 * 0.1 = ~25)
  Serial.begin(115200);
  Serial.println("FastLED Test");
}

void loop() {
  fill_solid(leds, NUM_LEDS, CRGB::Red);
  Serial.println("Red");
  FastLED.show();
  delay(1000);

  fill_solid(leds, NUM_LEDS, CRGB::Green);
  Serial.println("Green");
  FastLED.show();
  delay(1000);

  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  Serial.println("Blue");
  FastLED.show();
  delay(1000);
}
