import time
start_time = 0

last_time = 0

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
    # print(1 / (next_time - time.time()))
    try:
        time.sleep(next_time - time.time())
    except ValueError:
        pass
    last_time = time.time()