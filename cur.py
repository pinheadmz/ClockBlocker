import time
import curses
import atexit

def cleanup():	
	# reset all this crap to normal terminal settings
	curses.nocbreak()
	curses.echo()
	curses.endwin()
	print "bye!"
atexit.register(cleanup)


# window object needed for getch()
stdscr = curses.initscr()

curses.start_color()
curses.noecho()
curses.halfdelay(50) # rest with nocbreak, blocking value is x 0.1 seconds

b = '%-25.24s%-27.26s%-20.19s%-20.19s' % ("234234521435","234234523626","53452562456","34523462345626")
stdscr.addstr(3, 3, b, curses.A_UNDERLINE)

'''
curses.init_pair(1, 0, 127)
while True:
	a = stdscr.getch()
	if a != -1:
		b = chr(a)
	else:
		b = " "
	stdscr.addstr(3, 3, b, curses.color_pair(1))
'''

'''
y = 0
x = 0
for c in range(254):
	curses.init_pair(c + 1, 0, c)
	s = "#0 " + str(c) + " "
	stdscr.addstr(y, x, s, curses.color_pair(c))

	if x < 40:
		x += 7
	else:
		x = 0
		y += 1
'''
'''
for c in range(255):
	curses.init_pair(c, c, 0)
	s = "#" + str(c) + " 0 "
	stdscr.addstr(y, x, s, curses.color_pair(1))
	
	if x < 40:
		x += 7
	else:
		x = 0
		y += 1
'''
stdscr.refresh()
time.sleep(30)


