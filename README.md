# SyncMyLEDs

## Requirements and Installation
Requires Python and the following modules

    websocket-client   
    numpy
    mss
    argparse

Install requirements by running pip install -r requirements.txt

## Usage
You can use the bat file, which contains the line below, or type similarly in the terminal

    python rgbcontrol.py -b 0.2 -l 192.168.1.61:81 -f 0.9
    
To use defaults
    
    python rgbcontrol.py default

To manually set up the parameters
    
    python rgbcontrol.py

### Arguments
-l IP address:port for your strip

-f complementary factor for smoother transitions, but worsen response for flashing images

-b control brighness, would recommend you stick between 0-1

Alternatively, you can modify these variables in the User Setup part of rgbcontrol.py

## Issues
FPS target doesnt work right now, if you have a fix, start a PR

## This works only with the project linked below
    https://github.com/wirekraken/ESP8266-Websockets-LED
