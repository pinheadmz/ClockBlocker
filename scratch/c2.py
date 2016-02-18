#!/usr/bin/env python
# Copyright (C) 2006 by Johannes Zellner, <johannes@zellner.org>
# modified by mac@calmar.ws to fit my output needs
# modified by crncosta@carloscosta.org to fit my output needs

import sys
import os

def echo(msg):
    os.system('echo -n "' + str(msg) + '"')

def out(n):
    os.system("tput setab " + str(n) + "; echo -n " + ("\"% 4d\"" % n))
    os.system("tput setab 0")

# normal colors 1 - 16
os.system("tput setaf 16")
for n in range(8):
    out(n)
echo("\n")
for n in range(8, 16):
    out(n)

echo("\n")
echo("\n")

y=16
while y < 231:
    for z in range(0,6):
        out(y)
        y += 1

    echo("\n")


echo("\n")

for n in range(232, 256):
    out(n)
    if n == 237 or n == 243 or n == 249:
        echo("\n")

echo("\n")
os.system("tput setaf 7")
os.system("tput setab 0")

'''


import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    try:
        for i in range(0, 255):
            stdscr.addstr(str(i)+" ", curses.color_pair(i))
    except curses.ERR:
        # End of screen reached
        pass
    stdscr.getch()

curses.wrapper(main)
'''
