#Petty
**the next generation pet carer.**
***作者： 石 政宇   && 方 宇阳***
*如有问题，请联系shizhengyu93@hotmail.com.*
****
##对于开发者：
###启动注意事项
	1.修改src/main.py中volatile项。
>一般来说，推断的顺序为：
>>arduino（电机） -> bluno(rx灯) -> uno（排除）
>>摄像头（发亮者）

	2.ifconfig查看地址
	3.程序需以su运行。
	4.如遇程序意外退出，请尽量重启，或手动结束mjpg_streamer程序。
###检查顺序
	1.网路链接
	2.蓝牙连接（灯）
	3.rk3399供电
	4.电机运转
	5.摄像头灯
	6.修改、启动主程序
	7.确认程序版本
	8.遥控状况
	9.HTTP链接
	10.避障