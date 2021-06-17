import numpy as np
from mss import mss
import argparse
from websocketutils import *
from timecheck import *

# user setup default, can use arguments to override
link = 'ws://192.168.1.61:81/'
factor = 0.97       # how much of the old value to use 
brightness = 0.2
image_width = 2560
fps_target = 120    # NOT WORKING, timerdelay function causes unreliable fps

# Cropped image dimensions and location
width_to_factor = 2000
height_padding = 100
height_to_factor = 2

# calc
width_centre = int(image_width / 2)
half_width_to_factor = int(width_to_factor / 2)
y1, y2 = (width_centre - half_width_to_factor), (width_centre + half_width_to_factor)
x1, x2 = (height_padding), (height_padding + height_to_factor)
delay_target = 1 / fps_target
bbox = (x1, y1, x2, y2)
# fps_target=2/(A2+0.0008)^0.6
# delay = (2/fps_target)^(1/0.6)
# print(delay)

def main():
    parseargs()
    ws = wsConnect(link)
    old = [0, 0, 0] 
    old2 = [0, 0, 0] 
    try:
        frames = 0
        while True:

            # Take a screenshot
            # Get raw pixels from the screen
            ss = np.array(mss().grab(bbox))
            ss = ss[:, :, 0:3]

            # generate new rgb colors
            new = generateNewRGB(ss)
            rgb = comfilter(new, old)
            if rgb != new:
                brightnesscorrectedrgb = tuple(int(val * brightness) for val in rgb)
                sendrgb(ws, brightnesscorrectedrgb, printx=False)
                frames += 1
            if updateFPS():
                print(frames, 'Hz', new, old, rgb, end='\r')
                frames = 0
            old = rgb
            old2 = new

    except KeyboardInterrupt:
        print("\nExiting.")
        wsSend(ws, '#000000')
        wsClose(ws)

def generateNewRGB(image):
    # calculate average rgb values
    average = [0, 0, 0]
    count = 0
    x = 1

    for row in image:
        for r, g, b in row:
            if x == 3:              # take one in x pixel values to speed things up
                average[0] += r
                average[1] += g
                average[2] += b
                count += 1
                x = 0
            else:
                x += 1

    for i in range(3):
        average[i] = int(average[i] / count)

    correct_sequence = (average[2], average[1], average[0])     # bgr to rgb
    return correct_sequence

def sendrgb(ws, rgb, printx):
    # send hex value to the websocket
    message = '#' + '%02x%02x%02x' % rgb
    wsSend(ws, message)
    if printx == True:
        print(message)

def comfilter(new, old):
    # complementary filter, return value as a weighted average of the new and old values, to smooth transition
    filtered = [int(old[i] * factor + new[i] * (1 - factor)) for i in range(3)]
    return filtered

def parseargs():
    parser = argparse.ArgumentParser(description='Sync websockets LED strip with action on screen.')
    
    parser.add_argument("-l", "--Link", help = "Local IP:Port address of the ESP running the websockets LED", required = False)
    parser.add_argument("-f", "--Factor", help = "Complementary filter factor, higher will be smoother, but longer response time, 0-1", required = False)
    parser.add_argument("-b", "--Brightness", help = "Brightness, 0-1", required = False)

    args = parser.parse_args()

    if args.Link:
        global link
        link = "ws://" + args.Link + '/'
        print(link)
    if args.Brightness:
        brightnesscheck = float(args.Brightness)
        if brightnesscheck > 0 and brightnesscheck < 1:
            global brightness
            brightness = brightnesscheck
        else:
            "Invalid brightness setting, using default (0.2)"

if __name__ == '__main__':
    main()
