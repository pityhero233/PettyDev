#include "include/rplidar.h"
#include "include/rplidar_driver.h"
#include <iostream>
#include <cstdio>

using namespace std;
using namespace rp::standalone::rplidar;
RPlidarDriver* drv = RPlidarDriver::CreateDriver(DRIVER_TYPE_SERIALPORT);//init the driver
int main(){
    auto result = RPlidarDriver::connect("/dev/ttyUSB1",115200,0);
    cout<<"connected. begin\n";
    drv->startMotor();

    RPlidarDriver::DisposeDriver(drv);//release the driver
    return 0;
}