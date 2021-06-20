import numpy as np
from mss import mss
import argparse
from websocketutils import *
from timecheck import *
import sys

# user setup default, can use arguments to override
link = 'ws://192.168.1.61:81/'
factor = 0.98       # how much of the old value to use 
brightness = 0.95
image_width = 2560
fps_target = 120    # NOT WORKING, timerdelay function causes unreliable fps
maxdelta = 0.3
timeout = 60    # seconds

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
    old = [float(0)] * 3 
    try:
        frames = 0
        active = True
        off = False
        while True:
            # Take a screenshot (bgr)
            ss = np.array(mss().grab(bbox))
            ss = ss[:, :, 0:3]

            # generate new rgb colors
            new = generateNewRGB(ss, old)
            rgb = comfilter(new, old)
            delrgb = checkdelta(rgb, old)
            # send rgb
            if delrgb != old:
                if off == True:
                    switch_lights(ws, delrgb, 'on')
                active = True

                brightnesscorrectedrgb = tuple(int(val * brightness) for val in delrgb)
                sendrgb(ws, brightnesscorrectedrgb, printx=False)
                frames += 1
                off = False

            else:
                if active == True:
                    time_since_update = time.time()
                active = False
                if time.time() - time_since_update > timeout and off == False:
                    switch_lights(ws, delrgb, 'off')
                    off = True

            # display fps
            if updateFPS():
                if frames < 100:
                    print('  ', end='')
                elif frames < 10:
                    print(' ', end='')
                print(frames, 'Hz', end='\r')
                frames = 0

            old = delrgb

    except KeyboardInterrupt:
        print("\nExiting.")
        
        # soft off
        if off == False:
            switch_lights(ws, delrgb, 'off')

        wsClose(ws)

def generateNewRGB(image, old):
    # calculate average rgb values
    average = [float(0)] * 3
    count = 0
    x = 1

    # sum
    for row in image:
        for r, g, b in row:
            if x == 3:              # take one in x pixel values to speed things up
                average[0] += b
                average[1] += g
                average[2] += r
                count += 1
                x = 0
            else:
                x += 1

    # average
    for i in range(3):
        average[i] = float(average[i] / count)
        
    return average

def checkdelta(new, old):
    # check if max delta is not exceeded, for smoother transitions
    delta = [float(0)] * 3
    checked = [float(0)] * 3
    for i in range(3):
        delta[i] = new[i] - old[i]
        if abs(delta[i]) > maxdelta:
            if delta[i] > 0:
                checked[i] = old[i] + maxdelta
            else:
                checked[i] = old[i] - maxdelta
        else:
            checked[i] = new[i]

    return checked

def comfilter(new, old):
    # complementary filter, return value as a weighted average of the new and old values, to smooth transition
    filtered = [round(old[i] * factor + new[i] * (1 - factor) + 0.5, 3) for i in range(3)]
    return filtered

def sendrgb(ws, rgb, printx):
    # send hex value to the websocket
    message = '#' + '%02x%02x%02x' % rgb
    wsSend(ws, message)
    if printx == True:
        print(message, rgb)

def parseargs():
    try:
        if sys.argv[1] == 'default':
            usedefault = True
        else:
            usedefault = False
    except:
        usedefault = False
    
    if usedefault == False:
        parser = argparse.ArgumentParser(description='Sync websockets LED strip with action on screen.')
    
        parser.add_argument("-l", "--Link", help = "Local IP:Port address of the ESP running the websockets LED", required = False)
        parser.add_argument("-f", "--Factor", help = "Complementary filter factor, higher will be smoother, but longer response time, 0-1", required = False)
        parser.add_argument("-b", "--Brightness", help = "Brightness, 0-1", required = False)

        args = parser.parse_args()
        if args.Link:
            global link
            link = "ws://" + args.Link + '/'
        else:
            linkin = input(f"Link:Port (Default {link}): ")
            if linkin != '':
                link = linkin
                
        if args.Brightness:
            brightnesscheck = float(args.Brightness)
            if brightnesscheck > 0 and brightnesscheck < 1:
                global brightness
                brightness = brightnesscheck
            else:
                "Invalid brightness setting, using default (0.2)"
        else:
            bin = input(f'Brightness (0-1) (Default {brightness}): ')
            if bin != '':
                bin = float(bin)
                if inlimits(bin):
                    brightness = bin
            
        if args.Factor:
            global factor
            factor = float(args.Factor)
        else:
            factorin = input(f"Factor (0-1) (Default {factor}): ")
            if factorin != '':
                factorin = float(factorin)
                if inlimits(factorin):
                    print(factorin)
                    factor = factorin
                else:
                    print('value invalid')
    else:
        print('Using defaults:')
        print(f'\t{link=        }')
        print(f'\t{brightness=  }')
        print(f'\t{factor=      }')

def inlimits(num):
    if num >= 0 and num <= 1:
        return True
    return False

def switch_lights(ws, delrgb, command):
    offlen = 120
    irange = list(range(offlen))
    
    # change list based on command
    if command == 'off':
        irange.sort(reverse=True)
        state = 0
    else:
        state = 1

    # soft to command
    for i in irange:
        color = tuple(int(col * (i / offlen)) for col in delrgb)
        sendrgb(ws, color, printx=False)

    # confirm state
    sendrgb(ws, tuple(int(col * state) for col in delrgb), printx=False)


if __name__ == '__main__':
    main()
