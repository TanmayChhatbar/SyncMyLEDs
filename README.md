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
You'll want to modify the -l IP address:port for your strip
Based on your preference, higher number for -f will allow smoother transitions, but worsen response for flashing images
Modify -b to control brighness, would recommend you stick between 0-1
    python rgbcontrol.py -b 0.2 -l 192.168.1.61:81 -f 0.9
Alternatively, you can modify these variables in the User Setup part of rgbcontrol.py

## Issues
FPS target doesnt work right now, if you have a fix, start a PR

## This works only with the project linked below
https://github.com/wirekraken/ESP8266-Websockets-LED
