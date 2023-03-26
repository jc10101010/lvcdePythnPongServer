import sys
import socket
import selectors
import types
import time
import math
import random


def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"SERVER: Server has accepted connection from client {addr}.")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask, paddle1, paddle2, ball, gm):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:

        if gm.state == 0:
            for i in range(len(gm.queue)):
                if gm.queue[i] == data.addr:
                    data.outb = b"CONFIRMED JOIN\n"
                    gm.state = 1

        recv_data = sock.recv(1024)
        if recv_data:
            cmc = recv_data.decode()
            #print(f"SERVER: Server has received information from the client {data.addr}:  \n", cmc.split("\n"))
            lines = cmc.split("\n")
            for line in lines:
                sln = line.split(" ")
                if sln[0] == "REQUEST":
                    if sln[1] == "JOIN":
                        if gm.paddle1add != data.addr and gm.paddle2add != data.addr and data.addr not in gm.queue:
                            if gm.paddle1add == "":
                                data.outb += b"CONFIRM JOIN\n"
                                gm.paddle1add = data.addr
                                if gm.paddle2add != "":
                                    gm.state = 1
                            elif gm.paddle2add == "":
                                data.outb += b"CONFIRM JOIN\n"
                                gm.paddle2add = data.addr
                                if gm.paddle1add != "":
                                    gm.state = 1
                            else:
                                data.outb += b"WAIT\n"
                                found = False
                                for i in range(len(gm.queue)):
                                    add = gm.queue[i]
                                    if add == "":
                                        found = True
                                        gm.queue[i] = data.addr
                                if found == False:
                                    gm.queue.append(data.addr)
                    elif sln[1] == "POS":
                        if gm.paddle2add == data.addr:
                            data.outb += "CONFIRM POS {0},{1}\n".format(-paddle1.pos[0], paddle1.pos[1]).encode()
                        elif gm.paddle1add == data.addr:
                            data.outb += "CONFIRM POS {0},{1}\n".format(paddle2.pos[0], paddle2.pos[1]).encode()
                    elif sln[1] == "BPOS":
                        if data.addr == gm.paddle1add or data.addr == gm.paddle2add:
                            data.outb += "CONFIRM BPOS {0},{1}\n".format(ball.pos[0], ball.pos[1]).encode()
                elif sln[0] == "SET":
                    if sln[1] == "POS":
                        if gm.paddle2add == data.addr:
                            vals = sln[3].decode().split(",")
                            paddle2.pos = [-float(vals[0]), float(vals[1])]
                        elif gm.paddle1add == data.addr:
                            vals = sln[3].decode().split(",")
                            paddle1.pos = [float(vals[0]), float(vals[1])]
        else:
            print(f"SERVER: Closing connection to the client {data.addr}.")
            if gm.paddle1add == data.addr:
                gm.paddle1add = ""
                gm.state = 0
            elif gm.paddle2add == data.addr:
                gm.paddle2add = ""
                gm.state = 0
            else:
                for i in range(len(gm.queue)):
                    if gm.queue[i] == data.addr:
                        gm.queue[i] = ""
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            #print(f"SERVER: Server is sending information to the client {data.addr}: \n", (data.outb).decode().split("\n"))
            sent = sock.send(data.outb) 
            data.outb = data.outb[sent:]

def cosd(a):
    return math.cos(a/180 * math.pi)
def sind(a):
    return math.sin(a/180 * math.pi)
   
def seconds():
    return time.time_ns() / 1000000000

def handleWallEndCollisions(ball, gm):
    if ball.pos[0] < (-WIDTH/2) + ball.radius - ball.radius/3:
        gm.score += 1
        print(gm.score)
    elif ball.pos[0] > (WIDTH/2) - ball.radius + ball.radius/3:
        gm.score -= 1
        print(gm.score)

def handleWallOtherCollisions(ball):
    if ball.pos[1] < (-HEIGHT/2) + ball.radius:
        ball.angle = (ball.angle - 90) + random.randint(-15, 15)
    elif ball.pos[1] > (HEIGHT/2) - ball.radius:
        ball.angle = (ball.angle - 90) + random.randint(-15, 15)

def handlePaddleCollisions(ball, paddle1, paddle2):
    ballSideLength = ball.radius * 2/3
    c1 = False
    c2 = False
    #Paddle one
    if abs(paddle1.pos[0] - ball.pos[0]) > paddle1.width/2 + ballSideLength/2:
        c1 = True
    if abs(paddle1.pos[1] - ball.pos[1]) > paddle1.height/2 + ballSideLength/2:
        c2 = True
    
    if not c1 and not c2:
        ball.angle = (ball.angle - 90) + random.randint(-15, 15)
    
    c1 = False
    c2 = False
    #Paddle two
    if abs(paddle2.pos[0] - ball.pos[0]) > paddle2.width/2 + ballSideLength/2:
        c1 = True
    if abs(paddle2.pos[1] - ball.pos[1]) > paddle2.height/2 + ballSideLength/2:
        c2 = True
    
    if not c1 and not c2:
        ball.angle = (ball.angle - 90) + random.randint(-15, 15)

    


#Pong server setup
WIDTH = 1000
HEIGHT = 700

class Paddle():
    def __init__(self):
        self.pos = [WIDTH,0]
        self.width = 20
        self.height = 130
        self.distWall = 55
        self.speed= 15


class Ball():
    def __init__(self):
        self.pos = [0,0]
        self.radius = 15
        self.angle = 90
        self.speed = 500
        self.velocity = [0, self.speed]
        self.velocityR = [self.speed, 0]
    
    def rotateVelocity(self):
         a = self.angle
         v = self.velocity
         a2 = 360 - a
         self.velocityR = [cosd(a2) * v[0] - sind(a2) * v[1], sind(a2) * v[0] + cosd(a2) * v[1]]

class GameManager():
    def __init__(self):
        self.paddle1add = ""
        self.paddle2add = ""
        self.queue = []
        self.state = 0
        self.score = 0
        self.scoreMax = 5
        self.nextAdd = ""

#Pygame setup
paddle1 = Paddle()
paddle2 = Paddle()
ball = Ball()
gm = GameManager()


#Network setup
sel = selectors.DefaultSelector()
host, port = #
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
s.listen()
print(f"SERVER: Server listening on {(host, port)}.")
s.setblocking(False)
sel.register(s, selectors.EVENT_READ, data=None)

timePrevious = seconds() 
try:
    while True:
        print("\n" * 15, "PADDLE 1: ", gm.paddle1add)
        print("PADDLE 2: ", gm.paddle2add)
        print("QUEUE: ", gm.queue)
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask, paddle1, paddle2, ball, gm)
        if gm.state == 1:
            #Move ball and check for ball collisions
            timeCurrent = seconds()
            ball.rotateVelocity()
            ball.pos[0] += ball.velocityR[0] * (timeCurrent - timePrevious)
            ball.pos[1] += ball.velocityR[1] * (timeCurrent - timePrevious)
            timePrevious = seconds()

            #Paddle collisions handle
            handlePaddleCollisions(ball, paddle1, paddle2)
            #Wall collisions handle
            handleWallEndCollisions(ball, gm)
            handleWallOtherCollisions(ball)
            
            if abs(gm.score) == gm.scoreMax:
                break
        
            

        
except KeyboardInterrupt:
    print("SERVER: Server caught keyboard interrupt, exiting.")
finally:
    sel.close()
