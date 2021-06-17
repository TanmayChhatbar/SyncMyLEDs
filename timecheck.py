import time
start_time = 0
last_time = 0
nextupdatetime = 0

def timerCheck():
    # checks time elapsed between simulatenous calling of the function
    global start_time
    timetaken = time.time() - start_time
    start_time = time.time()
    return round(timetaken, 5)

def timerDelay(delay_target):
    # delay to target a certain fps
    global last_time
    next_time = last_time + delay_target
    current_time = time.time()
    delay = next_time - current_time
    if delay > 0:
        time.sleep(delay / 2)           # time.sleep isnt accurate, so just arbitrary cut the delay to half
        # print(f"{next_time=}\t{last_time=}\t\t{delay}")
    else:
        print(f"\n{next_time=}\t{current_time=}\t{last_time=}")
    last_time = time.time()

def updateFPS():
    global nextupdatetime
    current_time = time.time()
    if current_time > nextupdatetime:
        nextupdatetime = current_time + 1
        return True
    return False