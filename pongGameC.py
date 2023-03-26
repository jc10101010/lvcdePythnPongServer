import sys
import socket
import pygame
import types

from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

#Client configuration
sendOut = b""
host, port = #
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
s.sendall(b"REQUEST JOIN")
rsp2 = s.recv(1024)
while True:
    rsp2 = rsp2.decode()
    rsp = rsp2.split("\n")[0]
    rsp = rsp.split(" ")
    if rsp[0] == "CONFIRM" and rsp[1] == "JOIN":
        print("CLIENT: Connection confirmed. Game started.")
        break
    elif rsp[0] == "WAIT":
        print("CLIENT: Waiting in queue.")
        rsp2 = s.recv(1024)
    else:
        sys.exit("CLIENT: Client detects an invalid response from the server, developer please fix.")
s.settimeout(1/60)

#Pygame configuration
pygame.init()
clock = pygame.time.Clock()
WIDTH = 1000
HEIGHT = 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
running = True

def set_position(a, b, w, h, sw, sh):
    a.x = b[0] - (w/2) 
    a.y = b[1] - (h/2) + sh/2

#Standard values
paddleWidth = 20
paddleHeight = 130
paddleInitialDistWall = 55
paddleSpeed = 15
ballRadius = 15


#Game configuration
paddleMainPos = [paddleInitialDistWall,0]
paddleSecondaryPos = [WIDTH - paddleInitialDistWall,0]
ballPos = [0,0]
paddleMain = pygame.Rect(paddleMainPos, (paddleWidth, paddleHeight))
paddleSecondary = pygame.Rect(paddleSecondaryPos, (paddleWidth, paddleHeight))
game_state = 1

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print("CLIENT: Client quits game and ends connection.")
            running = False
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                print("CLIENT: Client quits game and ends connection.")
                running = False

    keys_pressed = pygame.key.get_pressed()

    if keys_pressed[K_UP]:
        paddleMainPos[1] -= paddleSpeed
    if keys_pressed[K_DOWN]:
        paddleMainPos[1] += paddleSpeed

    #Limit position
    if paddleMainPos[1] < (-HEIGHT / 2) + paddleHeight/2:
        paddleMainPos[1] = (-HEIGHT / 2) + paddleHeight/2
    elif paddleMainPos[1] > (HEIGHT / 2) - paddleHeight/2:
        paddleMainPos[1] = (HEIGHT / 2) - paddleHeight/2
    
    #SEND NEW INFO
    sendOut += "SET {0},{1}\n".format( paddleMainPos[0], paddleMainPos[1]).encode()
    sendOut += "REQUEST POS\n".encode()
    sendOut += "REQUEST BPOS \n".encode()
    #print("CLIENT: Client has sent information to server: \n", sendOut.decode().split("\n"))
    
    #READ RESPONSE
    bytesSent = s.send(sendOut)
    if bytesSent == len(sendOut):
        try:
            msg = s.recv(1024)
            if len(msg) == 0:
                print('CLIENT: Server has disconnected.')
                sys.exit(0)
            else:
                #print("CLIENT: Client received message from server: \n", msg.decode().split())
                #If a valid response is received:
                lines = msg.decode().split("\n")
                for line in lines:
                    lns = line.split(" ")
                    if lns[0] == "CONFIRM":
                        if lns[1] == "POS":
                            vals = lns[2].split(",")
                            paddleSecondaryPos[0] = float(vals[0])
                            paddleSecondaryPos[1] = float(vals[1])
                        elif lns[1] == "BPOS":
                            vals = lns[2].split(",")
                            ballPos[0] = float(vals[0])
                            ballPos[1] = float(vals[1])
                        elif lns[1] == "STATE":
                            val = int(lns[3])
                            game_state = val

                
        except socket.timeout:
            print("CLIENT: Server did not respond fast enough.")
            continue
    sendOut = b""

    #Change visual positions
    set_position(paddleMain, paddleMainPos, paddleWidth, paddleHeight, WIDTH, HEIGHT)
    set_position(paddleSecondary, paddleSecondaryPos, paddleWidth, paddleHeight, WIDTH, HEIGHT)
    ballDisplayPos = [ballPos[0] + WIDTH/2, ballPos[1] + HEIGHT/2]
    #Draw objects
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (255, 255, 255), ballDisplayPos, ballRadius)
    pygame.draw.rect(screen, (255, 255, 255), paddleMain)
    pygame.draw.rect(screen, (255, 255, 255), paddleSecondary)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
s.close()
