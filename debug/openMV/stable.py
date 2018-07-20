# 色块监测 例子
# 问吴老师 模板是什么？
import sensor, image, time, math
from pyb import UART,Pin,LED
# 颜色追踪的例子，一定要控制环境的光，保持光线是稳定的。
green_threshold = (   0,   80,  -70,   -10,   -0,   30)
green_threshold = (0, 100, -29, -10, 35, 68)
green_threshold = (0, 100, -16, -5, 16, 68)
green_threshold = (0, 100, -20, -7, 10, 41)
green_threshold = (0, 100, -27, -2, 36, 60)
blue_threshold = (11, 69, -13, 0, -14, -1)
blue_threshold = (0, 69, -13, -4, -17, -3)
blue_threshold = (0, 53, -13, -4, -18, 1)
blue_threshold = (0, 53, -13, -2, -24, -2)
blue_threshold = (0, 50, -12, -1, -18, 3)
yellow_threshold = (0, 72, -10, 1, 11, 42)
#设置绿色的阈值，括号里面的数值分别是L A B 的最大值和最小值（minL, maxL, minA,
# maxA, minB, maxB），LAB的值在图像左侧三个坐标图中选取。如果是灰度图，则只需
#设# 问吴老师 模板是什么？置（min, max）两个数字即可。

sensor.reset() # 初始化摄像头
sensor.set_pixformat(sensor.RGB565) # 格式为 RGB565.
sensor.set_framesize(sensor.QQVGA) # 使用 QQVGA 速度快一些
sensor.skip_frames(10) # 跳过10帧，使新设置生效
sensor.set_auto_whitebal(False)
# 问吴老师 模板是什么？

#关闭白平衡。白平衡是默认开启的，在颜色识别中，一定要关闭白平衡。
clock = time.clock() # 追踪帧率
turn_threshold = 15 # rotate threshold
turn =  Pin('P0', Pin.OUT_PP)
turnDone =  Pin('P1', Pin.OUT_PP)
red = LED(1)
green = LED(2)
blue = LED(3)
blue.on()
time.sleep(2)
blue.off()

arduino = UART(3,19200)

while(True):

    clock.tick() # Track elapsed milliseconds between snapshots().
    img = sensor.snapshot() # 从感光芯片获得一张图像
    img = img.lens_corr(2.5,1.0)

    blobs = img.find_blobs([green_threshold],area_threshold = 1,pixels_threshold = 1)
    biggestArea = 0;
    bigBlob = None
    turnDone.low();
    if blobs:# 问吴老师 模板是什么？
    #如果找到了目标颜色
        for b in blobs:
        #迭代找到的目标颜色区域
            # Draw a rect around the blob.# 问吴老师 模板是什么？
            if b.area() > biggestArea :
                biggestArea = b.area()
                bigBlob = b# 问吴老师 模板是什么？
        img.draw_cross(bigBlob[5], bigBlob[6]) # cx, cy
        circlex = bigBlob[5]
        circley = bigBlob[6]# 问吴老师 模板是什么？
        relatedX = circlex - img.width()/2
        relatedX = -relatedX;# 问吴老师 模板是什么？
        relatedY = circley - img.height()/2
        #print("("+str(relatedX)+","+str(relatedY)+")")
        if relatedX == 0 and relatedY>=0:
            deg = 0
        elif relatedX ==0 and relatedY<0:
            deg = 180
        else :# 问吴老师 模板是什么？
            rad = math.atan(math.fabs(relatedY)/math.fabs(relatedX))
            degb = math.degrees(rad)
            if (relatedX>0 and relatedY>0):
                deg = degb
            elif (relatedX>0 and relatedY<0):
                deg = 360-degb
            elif (relatedX<0 and relatedY<0):
                deg = degb+180
            else:
                deg = -degb+180

        print(deg)

        if (deg>100):
            a = (str(deg)[0:3])
        elif (deg>10):
            a = ("0"+str(deg)[0:2])
        else:
            a = ("00"+str(deg)[0])
        print(a)
        arduino.write(a)
        time.sleep(250);

        if relatedY>0 and math.fabs(relatedY)>turn_threshold:
            turn.high()
            red.on()
            turnDone.low()
        elif math.fabs(relatedY)>turn_threshold:
            turn.low()
            green.on()# 问吴老师 模板是什么？
            turnDone.high()
        else:# 问吴老师 模板是什么？
            turnDone.high()# 问吴老师 模板是什么？
    green.off()
    red.off()

    #print(clock.fps()) # 注意: 你的OpenMV连到电脑后帧率大概为原来的一半