import numpy as np
from mss import mss
import argparse
from websocketutils import *
from timecheck import *
import sys

# user setup default, can use arguments to override
link = 'ws://192.168.1.88:81/'
factor = 0.97               # how much of the old value to use 
brightness = 0.8
image_width = 2560          # 1440p monitor
maxdelta = 10
timeout = 60                # seconds
min_brightness = 50         # need to uncomment a line in main function. lower brightness values will worsen smoothness when screen is dark
# fps_target = 120          # not working

# Cropped image dimensions and location (default settings for 1440p)
width_to_factor = 2000      # how much of the width to factor, centred
height_padding = 260        # how much of the top to ignore
height_to_factor = 1        # how much of the height to factor after the ignored pixels

# calc
width_centre = int(image_width / 2)
half_width_to_factor = int(width_to_factor / 2)
x1, x2 = (width_centre - half_width_to_factor), (width_centre + half_width_to_factor)
y1, y2 = (height_padding), (height_padding + height_to_factor)
bbox = (x1, y1, x2, y2)

# not working
# fps_target=2/(A2+0.0008)^0.6
# delay_target = 1 / fps_target
# delay = (2/fps_target)^(1/0.6)
# print(delay)

def main():
    parseargs()
    ws = wsConnect(link)

    try:
        frames = 0
        active = True
        off = False
        old = [float(0)] * 3
        oldsent = [float(0)] * 3

        while True:
            # Take a screenshot (bgr)
            ss = np.array(mss().grab(bbox))[:, :, 0:3]

            # generate new rgb colors
            rgb = comfilter(generateNewRGB(ss), old)
            delrgb = checkdelta(rgb, old)

            # send rgb
            if delrgb != old:
                active = True
                if off == True:
                    switch_lights(ws, delrgb, 'on')
                    off = False

                # correct for brightness multiplier    
                brightnesscorrectedrgb = tuple(int(val * brightness) for val in delrgb)
                
                # minimum brightness offset, uncomment next line to enable a minimum brightness
                # brightnesscorrectedrgb = tuple(int(min_brightness * (1 + val / 255)) for val in brightnesscorrectedrgb)
                if brightnesscorrectedrgb != oldsent:
                    oldsent = sendrgb(ws, brightnesscorrectedrgb, printx=False)
                frames += 1

            else:
                # check timeout
                if active == True:
                    time_since_update = time.time()
                    active = False
                elif time.time() - time_since_update > timeout and off == False:
                    switch_lights(ws, delrgb, 'off')
                    off = True

            # update fps in terminal
            frames = updateTerminal(frames, brightnesscorrectedrgb)

            old = delrgb

    except KeyboardInterrupt:
        print("\nExiting.")
        
        # soft off
        if off == False:
            switch_lights(ws, delrgb, 'off')

        wsClose(ws)

def generateNewRGB(image):
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

def comfilter(new, old):
    # complementary filter, return value as a weighted average of the new and old values, to smooth transition
    return [(old[i] * factor + new[i] * (1 - factor)) for i in range(3)]

def checkdelta(new, old):
    # check if max delta is not exceeded, for smoother transitions
    delta = 0.0
    checked = [float(0)] * 3

    for i in range(3):
        delta = new[i] - old[i]

        if abs(delta) > maxdelta:
            if delta > 0:
                checked[i] = old[i] + maxdelta
            else:
                checked[i] = old[i] - maxdelta
        else:
            checked[i] = new[i]

    return checked

def sendrgb(ws, rgb, printx):
    # send hex value to the websocket
    message = '#' + '%02x%02x%02x' %rgb
    wsSend(ws, message)
    if printx == True:
        print(message, rgb)
    return rgb

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

def updateTerminal(frames, color):
    if updateFPS():
        if frames < 100:
            print(' ', end='')
        elif frames < 10:
            print('  ', end='')
        print(' ', frames, 'Hz', ' ', end='')
        frames = 0
        print('\t', color, '    ', end='\r')
    return frames


if __name__ == '__main__':
    main()
