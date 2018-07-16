#Petty
**the next generation pet carer.**
***作者： 石 政宇   && 方 宇阳***
*如有问题，请联系shizhengyu93@hotmail.com.*
****
##对于开发者：
###启动注意事项
	1.修改src/main.py中volatile项。
>一般来说，推断的顺序为：
>>arduino（电机） -> bluno(rx灯)
	
	2.ifconfig查看rpi与rk3399地址
	3.修改rpi与rk3399中ip地址
	4.程序需以su运行,可以以ctrl-c停止执行。
	5.修改authorized_keys,为rpi添加权限。
###检查顺序
	0.ssh-key
>scp ~/.ssh/id_rsa.pub firefly@firefly.local:~/.ssh/authorized_keys

	1.网路链接
	2.蓝牙连接（灯）
	3.rk3399供电
	4.电机运转
	6.修改、启动主程序
	7.确认程序版本
	8.遥控状况
	9.HTTP链接
	10.避障