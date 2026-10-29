import numpy as np
import mss
import argparse
from websocketutils import *
from timecheck import *
import sys

# user setup default, can use arguments to override
link = 'ws://192.168.1.88:81/'
factor = 0.5               # how much of the old value to use 
brightness = 0.8
num_colors_to_send = 5      # number of horizontal screen zones, up to the strip's led count
led_count = 46              # match LED_COUNT in the firmware's src/config.h
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
    if not 1 <= num_colors_to_send <= min(led_count, width_to_factor):
        raise ValueError('number of colors must be between 1 and the LED count and capture width')
    ws = wsConnect(link)

    try:
        frames = 0
        active = True
        off = False
        old = [[0.0] * 3 for _ in range(num_colors_to_send)]
        oldsent = None
        delrgb = old
        brightnesscorrectedrgb = [tuple([0] * 3) for _ in old]
        screen = mss.MSS()

        while True:
            # Take a screenshot (bgr)
            ss = np.array(screen.grab(bbox))[:, :, 0:3]

            # generate new rgb colors
            sampled = generateZoneColors(ss, num_colors_to_send)
            delrgb = [checkdelta(comfilter(new, previous), previous)
                      for new, previous in zip(sampled, old)]

            # send rgb
            if delrgb != old or oldsent is None:
                active = True
                if off == True:
                    switch_lights(ws, delrgb, 'on')
                    off = False

                # correct for brightness multiplier    
                brightnesscorrectedrgb = [tuple(int(val * brightness) for val in color)
                                          for color in delrgb]
                
                # minimum brightness offset, uncomment next line to enable a minimum brightness
                # brightnesscorrectedrgb = [tuple(int(min_brightness * (1 + val / 255)) for val in color) for color in brightnesscorrectedrgb]
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

def generateZoneColors(image, count):
    # average each left-to-right zone and convert bgr to rgb
    return [zone.mean(axis=(0, 1))[::-1].tolist()
            for zone in np.array_split(image, count, axis=1)]

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

def sendrgb(ws, colors, printx):
    # send left-to-right hex colors to the websocket
    message = ','.join('#%02x%02x%02x' % tuple(color) for color in colors)
    wsSend(ws, message)
    if printx == True:
        print(message, colors)
    return colors

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
        parser.add_argument("-n", "--num-colors-to-send", type=int, help="number of screen zones (at most the strip's LED count)")

        args = parser.parse_args()
        if args.num_colors_to_send is not None:
            global num_colors_to_send
            num_colors_to_send = args.num_colors_to_send
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
        print(f'\t{num_colors_to_send=}')

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
        colors = [tuple(int(col * brightness * (i / offlen)) for col in color)
                  for color in delrgb]
        sendrgb(ws, colors, printx=False)

    # confirm state
    sendrgb(ws, [tuple(int(col * brightness * state) for col in color)
                 for color in delrgb], printx=False)

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
