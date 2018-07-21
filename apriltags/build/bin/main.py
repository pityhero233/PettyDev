import os
f = os.popen("./apriltags_demo ")
line = f.readline()
while line:
	d,x,y,z = line.split(" ")
	print y
	line = f.readline()

