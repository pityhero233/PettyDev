/* the AutoNavi System
 * based on apriltags and rplidar.
 * Copyright(c)2018 pityhero233.
 */
#include "rplidar.h" //RPLIDAR standard sdk, all-in-one header
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <cstring>
#include <assert.h>
#include <unistd.h>
#include <pthread.h>
using namespace std;
void clear(char* a){
    for(int i=0;i<sizeof(a);i++) a[i]=0;
}
//sock area
int client_sockfd;
int len;
struct sockaddr_in remote_addr; //remote address
unsigned int sin_size;
char buf[BUFSIZ];  //daata
char tmpbuf[2048];

float dist,x,y,z;

int init();
int sendSomething(char* sth);
int recvSomething(char* sth);

#ifndef _countof
#define _countof(_Array) (int)(sizeof(_Array) / sizeof(_Array[0]))
#endif

#ifdef _WIN32
#include <Windows.h>
#define delay(x)   ::Sleep(x)
#else
#include <unistd.h>
static inline void delay(_word_size_t ms){
    while (ms>=1000){
        usleep(1000*1000);
        ms-=1000;
    };
    if (ms!=0)
        usleep(ms*1000);
}
#endif

using namespace rp::standalone::rplidar;


void *chkAprilTags(void* ptr){
    FILE* pipe;pipe = popen("./apriltags_demo -d -D 1","r");
    assert(pipe);
    char tmp[1024];
    while (fgets(tmp,sizeof(tmp),pipe)!=NULL){
        if (tmp[strlen(tmp)-1]=='\n'){
            tmp[strlen(tmp)-1]='\0';
        }
        dist = atof(strtok(tmp," "));
        x = atof(strtok(NULL," "));
        y = atof(strtok(NULL," "));
        z = atof(strtok(NULL," "));
        printf("%f\n",dist);
    }
    pclose(pipe);
}

bool checkRPLIDARHealth(RPlidarDriver * drv)
{
    u_result     op_result;
    rplidar_response_device_health_t healthinfo;


    op_result = drv->getHealth(healthinfo);
    if (IS_OK(op_result)) { // the macro IS_OK is the preperred way to judge whether the operation is succeed.
        printf("RPLidar health status : %d\n", healthinfo.status);
        if (healthinfo.status == RPLIDAR_STATUS_ERROR) {
            fprintf(stderr, "Error, rplidar internal error detected. Please reboot the device to retry.\n");
            // enable the following code if you want rplidar to be reboot by software
            // drv->reset();
            return false;
        } else {
            return true;
        }

    } else {
        fprintf(stderr, "Error, cannot retrieve the lidar health code: %x\n", op_result);
        return false;
    }
}

#include <signal.h>
bool ctrl_c_pressed;
void ctrlc(int)
{
    ctrl_c_pressed = true;
}

int main(int argc, const char * argv[]) {
    init();
//    pthread_t id;
//    int ret = pthread_create(&id,NULL,chkAprilTags,NULL);
//    assert(!ret);
//    pthread_join(id,NULL);
//    printf("it's fine.");
    const char * opt_com_path = NULL;
    _u32         baudrateArray[2] = {115200, 256000};
    _u32         opt_com_baudrate = 115200;
    u_result     op_result;
    static int   thetaWanted;
    bool useArgcBaudrate = false;

    printf("Petty lidar System.\n"
           "Version: "RPLIDAR_SDK_VERSION"\n");
    sendSomething("Petty Lidar System.");
//
//    pthread_t id; // the id
//    int ret = pthread_create(&id,NULL,chkAprilTags,NULL);
//    if (argc>1) opt_com_path = argv[1];
    //thetaWanted = atoi(argv[1]);
//    printf("thetaWanted=%d\n",thetaWanted);
    useArgcBaudrate = true;

    if (!opt_com_path) {
#ifdef _WIN32
        // use default com port
        opt_com_path = "\\\\.\\com3";
#else
        opt_com_path = "/dev/ttyUSB0";
#endif
    }

    // create the driver instance
	RPlidarDriver * drv = RPlidarDriver::CreateDriver(DRIVER_TYPE_SERIALPORT);
    if (!drv) {
        fprintf(stderr, "insufficent memory, exit\n");
        exit(-2);
    }
    
    rplidar_response_device_info_t devinfo;
    bool connectSuccess = false;
    // make connection...
    if(useArgcBaudrate)
    {
        if(!drv)
            drv = RPlidarDriver::CreateDriver(DRIVER_TYPE_SERIALPORT);
        if (IS_OK(drv->connect(opt_com_path, opt_com_baudrate)))
        {
            op_result = drv->getDeviceInfo(devinfo);

            if (IS_OK(op_result)) 
            {
                connectSuccess = true;
            }
            else
            {
                delete drv;
                drv = NULL;
            }
        }
    }
    if (!connectSuccess) {
        
        fprintf(stderr, "Error, cannot bind to the specified serial port %s.\n"
            , opt_com_path);
//        goto on_finished;
    }

    // print out the device serial number, firmware and hardware version number..
    
    drv->startMotor();
    // start scan...
    drv->startScan(0,1);

    // fetech result and print it out...
    int tmp=0;
    while (1) {
        //main prog.
        printf("now ready to rcv.");

//        if (scanf("%d",&tmp)==1){
//            thetaWanted=tmp;
//        }
        clear(tmpbuf);
        recvSomething(tmpbuf);
        printf("new things received.");

        printf("%s\n",tmpbuf);
        tmp = atoi(tmpbuf);
        thetaWanted = tmp;
        rplidar_response_measurement_node_t nodes[8192];
        size_t   count = _countof(nodes);

        op_result = drv->grabScanData(nodes, count);
        printf("trying!");
        if (IS_OK(op_result)) {
            printf("IS OK!\n");
            drv->ascendScanData(nodes, count);
            bool flag = true;//in case of repetations
            for (int pos = 0; pos < (int)count ; ++pos) {
                float theta,dist;
                theta = (nodes[pos].angle_q6_checkbit >> RPLIDAR_RESP_MEASUREMENT_ANGLE_SHIFT)/64.0f;
                dist = nodes[pos].distance_q2/4.0f;
                if (abs(theta-thetaWanted)<=1&&flag){
                    printf("theta=%f,dist=%f\n",theta,dist);
                    strcpy(tmpbuf,"");
                    sprintf(tmpbuf,"%f",dist);
                    sendSomething(tmpbuf);
                    flag=false;
                }

//            }
        }

        if (ctrl_c_pressed){ 
            break;
        }
    }
    }
    drv->stop();
    drv->stopMotor();
    return 0;

    on_finished:
    RPlidarDriver::DisposeDriver(drv);
    drv = NULL;
}

int init(){

	memset(&remote_addr,0,sizeof(remote_addr)); //数据初始化--清零
	remote_addr.sin_family=AF_INET; //设置为IP通信
	remote_addr.sin_addr.s_addr=inet_addr("127.0.0.1");//服务器IP地址
	remote_addr.sin_port=htons(5555); //

	if((client_sockfd=socket(PF_INET,SOCK_DGRAM,0))<0)
	{
		perror("socket error");
		return 1;
	}
	return 0;
}
int sendSomething(char* sth){
	/* better */

	strcpy(buf,sth); // sending
	printf("sending: '%s'/n",buf);
	if((len=sendto(client_sockfd,buf,strlen(buf),0,(struct sockaddr *)&remote_addr,sizeof(struct sockaddr)))<0)
	{
		perror("recvfrom");
		return 1;
	}
	return 0;
}
int recvSomething(char* sth){
    clear(sth);clear(buf);
	recvfrom(client_sockfd, buf, 256, 0, (struct sockaddr*)&remote_addr, &sin_size);
	printf("%s\n",buf);
	strcpy(sth,buf);
        
	/*shut socket*/
	// close(clientt);
}

