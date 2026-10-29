/*
    sketch created on 30.11.2018 by Wirekraken
    https://github.com/wirekraken/ESP8266-Websockets-LED/tree/master/ESP8266-LED/data
*/
#include <Arduino.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <FS.h>
#include <SPIFFS.h>
#define FASTLED_ESP8266_RAW_PIN_ORDER
#include <FastLED.h>
#include "credentials.h"
#include "config.h"
#include "led_effects.h"

// initialize websocket on port 81
WebSocketsServer webSocket(81);
WebServer server(80);

// handle incoming messages
void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length)
{

    if (type == WStype_CONNECTED)
    {
        IPAddress ip = webSocket.remoteIP(num);

        String message = String("Connected");
        webSocket.broadcastTXT(message); // send the latest value to all clients on connection
    }

    if (type == WStype_TEXT)
    {
        String data;
        for (int x = 0; x < length; x++)
        {
            if (!isdigit(payload[x]))
                continue;
            data += (char)payload[x];
        }

        if (payload[0] == 'B')
        {
            flag = 0;
            Serial.print("Bright: ");
            bright = data.toInt();
            Serial.println(data);
            LEDS.setBrightness(bright);
        }
        else if (payload[0] == 'F')
        {
            flag = 0;
            Serial.print("Function: ");
            ledMode = data.toInt();
            Serial.println(data);
            ledEffect(ledMode);
        }
        else if (payload[0] == '#')
        {

            if (!flag)
            {
                Serial.print("flag : ");
                Serial.println(flag);
                ledMode = flag;
                ledEffect(ledMode);
                flag = 1;
            }
            else
            {
                // convert to a 24-bit color
                uint32_t rgb = (uint32_t)strtol((const char *)&payload[1], NULL, 16);

                // split into 8 bits per channel
                uint8_t r = (0 + (rgb >> 16) & 0xFF);
                uint8_t g = (0 + (rgb >> 8) & 0xFF);
                uint8_t b = (0 + (rgb >> 0) & 0xFF);

                Serial.print("ColorPicker: ");
                Serial.print(r);
                Serial.print(g);
                Serial.println(b);

                for (int x = 0; x < LED_COUNT; x++)
                {
                    leds[x].setRGB(r, g, b);
                }
                LEDS.show();
            }
        }
    }
}

// get the file type
String getContentType(String filename)
{
    if (server.hasArg("download"))
        return "application/octet-stream";
    else if (filename.endsWith(".htm"))
        return "text/html";
    else if (filename.endsWith(".html"))
        return "text/html";
    else if (filename.endsWith(".css"))
        return "text/css";
    else if (filename.endsWith(".js"))
        return "application/javascript";
    else if (filename.endsWith(".png"))
        return "image/png";
    else if (filename.endsWith(".gif"))
        return "image/gif";
    else if (filename.endsWith(".jpg"))
        return "image/jpeg";
    else if (filename.endsWith(".ico"))
        return "image/x-icon";
    else if (filename.endsWith(".xml"))
        return "text/xml";
    else if (filename.endsWith(".pdf"))
        return "application/x-pdf";
    else if (filename.endsWith(".zip"))
        return "application/x-zip";
    else if (filename.endsWith(".gz"))
        return "application/x-gzip";
    return "text/plain";
}

// find a file in the filesystem
bool handleFileRead(String path)
{
#ifdef DEBUG
    Serial.println("handleFileRead: " + path);
#endif
    if (path.endsWith("/"))
        path += "index.html";
    if (SPIFFS.exists(path))
    {
        File file = SPIFFS.open(path, "r");
        size_t sent = server.streamFile(file, getContentType(path));
        file.close();
        return true;
    }
    return false;
}

void setup()
{
    Serial.begin(115200);
    Serial.setTimeout(0);
    LEDS.setBrightness(bright);

    LEDS.addLeds<WS2812B, LED_DT, GRB>(leds, LED_COUNT); // configure the strip (WS2811, WS2812, WS2812B)
    // settings for your tape (tapes on WS2811, WS2812, WS2812B)
    updateColor(0, 0, 255);
    LEDS.show();

    WiFi.config(Ip, Gateway, Subnet);
    WiFi.begin(ssid, password);
    Serial.println("");

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }

    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());

    server.onNotFound([]()
                      {
        if (!handleFileRead(server.uri()))
          server.send(404, "text/plain", "FileNotFound"); });

    server.begin();

    if (!SPIFFS.begin(true))
    {
        Serial.println("SPIFFS mount/format failed");
        return;
    }

    webSocket.begin();
    webSocket.onEvent(webSocketEvent);
}

void loop()
{
    // handle HTTP and websocket requests
    webSocket.loop();
    server.handleClient();

    ledEffect(ledMode);
}
