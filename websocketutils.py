import websocket

def wsConnect(link):
    ws = websocket.WebSocket()
    print(f"Connecting to {link}", end='\r')
    ws.connect(link)
    print(ws.recv(), '')
    return ws

def wsSend(ws, val):
    ws.send(val)

def wsClose(ws):
    ws.close()