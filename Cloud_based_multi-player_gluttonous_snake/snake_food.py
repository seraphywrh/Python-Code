import pygame
import random


class Snake(object):
    # Initialize states. body = 5.
    def __init__(self, a):
        if a == 10:
            self.dirction = pygame.K_RIGHT
        else:
            self.dirction = pygame.K_LEFT
        self.body = []
        for x in range(10):
            self.addnode(a)

    # Add a node at the head of the snake.
    def addnode(self, a):
        left, top = (a, a)
        if self.body:
            left, top = (self.body[0].left, self.body[0].top)
        node = pygame.Rect(left, top, 10, 10)
        if self.dirction == pygame.K_LEFT:
            node.left -= 10
        elif self.dirction == pygame.K_RIGHT:
            node.left += 10
        elif self.dirction == pygame.K_UP:
            node.top -= 10
        elif self.dirction == pygame.K_DOWN:
            node.top += 10
        self.body.insert(0, node)

    # Delete a node at the tail
    def delnode(self):
        self.body.pop()

    # def isdead(self):
    #     # 撞墙
    #     if self.body[0].x not in range(SCREEN_X):
    #         return True
    #     if self.body[0].y not in range(SCR[EEN_Y):
    #         return True
    #     # 撞自己
    #     if self.body[0] in self.body[1:]:
    #         return True
    #     return False

    # Move forward.
    def move(self):
        self.addnode(0)
        self.delnode()

    # Change snake's direction but connot make a u-turn.
    def changedirection(self, curkey):
        LR = [pygame.K_LEFT, pygame.K_RIGHT]
        UD = [pygame.K_UP, pygame.K_DOWN]
        if curkey in LR + UD:
            if (curkey in LR) and (self.dirction in LR):
                return
            if (curkey in UD) and (self.dirction in UD):
                return
            self.dirction = curkey


class Food:
    def __init__(self):
        self.rect = pygame.Rect(-10, 0, 10, 10)

    def remove(self):
        self.rect.x = -10

    def set(self):
        if self.rect.x == -10:
            allpos = []
            # Don't go too close to the wall. between 25 ~ SCREEN_X-25
            for pos in range(30, 600 - 30, 10):
                allpos.append(pos)
            self.rect.left = random.choice(allpos)
            self.rect.top = random.choice(allpos)
            #print(self.rect)

