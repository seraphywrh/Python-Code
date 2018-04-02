import zmq
import pygame
import sys
import random
from snake_food import Snake
from snake_food import Food
from pygame.locals import *
import time
SCREEN_X = 600
SCREEN_Y = 600


def isdead(my_id, snakes):
    # 撞墙
    if snakes[my_id].body[0].x not in range(SCREEN_X):
        return True
    if snakes[my_id].body[0].y not in range(SCREEN_Y):
        return True
    # 撞自己
    for key in snakes.keys():
        if snakes[my_id].body[0] in snakes[key].body[1:]:
            return True
    return False

def text_to_screen(screen, text, x, y, size = 50,
            color = (200, 000, 000)):

        text = str(text)
        font = pygame.font.Font( size)
        text = font.render(text, True, color)
        screen.blit(text, (x, y))

context = zmq.Context()
socket1 = context.socket(zmq.PUB)
socket2 = context.socket(zmq.SUB)
socket1.connect("tcp://localhost:5051")
socket2.setsockopt(zmq.RCVTIMEO, 500)
socket2.connect("tcp://localhost:5050")
socket2.setsockopt_string(zmq.SUBSCRIBE, '')

#开始界面
pygame.init()
pygame.font.init()
screen_size = (SCREEN_X, SCREEN_Y)
screen = pygame.display.set_mode(screen_size)
#print text
myfont = pygame.font.SysFont('Big', 25)
myfont1 = pygame.font.SysFont('Small', 15)
welcome = myfont.render('Welcome To Gluttonous Snake !',False,(255,0,255))
choose1 = myfont.render('Press <- to choose BULE snake', False, (0, 255, 255))
choose2 = myfont.render('Press -> to choose GREEN snake', False, (0, 255, 0))
#print snakes
background = pygame.Surface(screen_size)
pygame.draw.rect(background,(0,255,255),(100,250,125,25))
pygame.draw.rect(background,(0,255,0),(375,250,125,25))
screen.blit(background,(0,0))
screen.blit(choose1,(50,200))
screen.blit(choose2,(325,200))
screen.blit(welcome,(150,100))
g_image = pygame.image.load('green.png')
screen.blit(g_image,(350,290))
b_image = pygame.image.load('blue.png')
screen.blit(b_image,(50,260))
#显示
pygame.display.update()      #update
pygame.display.set_caption('Snake')
clock = pygame.time.Clock()

#snake初始化
snakes = {}
snake0 = Snake(10)
snake1 = Snake(590)
snakes['b'] = snake0
snakes['g'] = snake1
my_id = 'x'

#是否死了
dead = {'b':False,'g':False}

#分数
scores = {'b':0,'g':0}

#food初始化
foodrect = []

cur = 0
while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            print("key_down")
            if event.key == pygame.K_LEFT:
                my_id = 'b'
                socket1.send_string("id_confirmed")
                #print("x")
            elif event.key == pygame.K_RIGHT:
                socket1.send_string("id_confirmed")
                my_id = 'g'
                #print("x")
    if my_id == 'b' or my_id == 'g':
        break


yourchoice = myfont.render('Your choice',False,(255,0,0))
if my_id == 'b':
    screen.blit(yourchoice,(100,500))
elif my_id == 'g':
    screen.blit(yourchoice,(375,500))

pygame.display.flip()


while True:
    try:
        start_signal = socket2.recv_string()
    except zmq.ZMQError or zmq.error.Again:
        continue
    print("start_signal " + start_signal)
    if start_signal == "start":
        break


for i in range(5):
    food = Food()
    food.set()
    socket1.send_string("put %d %d %d %d" % (food.rect.left, food.rect.top, 10, 10))


while True:
    try:
        string = socket2.recv_string()
    except zmq.ZMQError or zmq.error.Again:
        pass
    else:
        msg_type = string.split()[0]
        if msg_type == 'move':
            if string.split()[2] == 'moveleft':
                direction = pygame.K_LEFT
            elif string.split()[2] == 'moveright':
                direction = pygame.K_RIGHT
            elif string.split()[2] == 'moveup':
                direction = pygame.K_UP
            else:
                direction = pygame.K_DOWN
            snakes[string.split()[1]].changedirection(direction)

        elif msg_type == 'put':
            left = int(string.split()[1])
            top = int(string.split()[2])
            #新食物
            new_food = Food()
            new_food.rect = pygame.Rect(left, top, 10, 10)
            foodrect.append(new_food.rect)
        elif msg_type == 'remove':
            left = int(string.split()[1])
            top = int(string.split()[2])
            #被吃掉的食物
            rect = pygame.Rect(left, top, 10, 10)
            foodrect.remove(rect)
            snakes[string.split()[5]].addnode(0)
            scores[string.split()[5]] += 50
        elif msg_type == 'dead':
            dead_id = string.split()[1]
            dead[dead_id] = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            socket1.send_string("die %c" % my_id)
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                socket1.send_string("move %c moveleft" % my_id)
            elif event.key == pygame.K_RIGHT:
                socket1.send_string("move %c moveright" % my_id)
            elif event.key == pygame.K_UP:
                socket1.send_string("move %c moveup" % my_id)
            elif event.key == pygame.K_DOWN:
                socket1.send_string("move %c movedown" % my_id)

    screen.fill((0,0,0))


    # 显示死亡文字
    if isdead(my_id, snakes) and dead[my_id]==False:
        socket1.send_string("dead " + my_id)
        if (True in dead.values()):
            dietext = myfont.render('YOU WIN!', False, (255, 0, 0))
            screen.blit(dietext, (200, 280))
            pygame.display.update()
        else:
            dietext = myfont.render('YOU DEAD!',False,(255,0,0))
            screen.blit(dietext,(200,280))
            pygame.display.update()
    # 食物处理 / 吃到+50分
    # 当食物rect与蛇头重合
    if snakes[my_id].body[0] in foodrect:
        #吃掉
        socket1.send_string("remove %d %d %d %d %c" % (snakes[my_id].body[0].left,snakes[my_id].body[0].top, 10, 10,my_id))
        #显示
        cur = pygame.time.get_ticks()
        #Snake增加一个Node，加分
        #socket1.send_string("add %c" % my_id)
        #补食物
        new_food = Food()
        new_food.set()
        socket1.send_string("put %d %d %d %d" % (new_food.rect.left, new_food.rect.top, 10, 10))


    for f in foodrect:
        red = random.choice(range(255))
        green = random.choice(range(255))
        blue = random.choice(range(255))
        pygame.draw.rect(screen, (red, green, blue), f, 0)
    if cur != 0 and pygame.time.get_ticks() - cur < 2000:
        eat = myfont.render('+50', False, (255, 0, 0))  #显示加分
        screen.blit(eat, (300, 20))
    for id in dead.keys():
        if not dead[id]:
            snakes[id].move()
            if id == 'g':
                for rect in snakes[id].body:
                    pygame.draw.rect(screen, (0,255,0), rect, 0)
            else:
                for rect in snakes[id].body:
                    pygame.draw.rect(screen, (0,255,255), rect, 0)
            scores[id] += pygame.time.get_ticks() / 100
    score_t1 = myfont1.render('blue snake:%d' % scores['b'], False, (0, 255, 255))  # 显示分数
    screen.blit(score_t1, (500, 550))
    score_t2 = myfont1.render('green snake:%d' % scores['g'], False, (0, 255, 0))
    screen.blit(score_t2, (500, 560))
    if not dead[my_id]:
        pygame.display.update()
    clock.tick(10)
