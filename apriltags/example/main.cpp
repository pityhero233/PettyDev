/* the AutoNavi System
 * based on apriltags and rplidar.
 * Copyright(c)2018 pityhero233.
 */


#include <stdio.h>
#include <stdlib.h>
#include <cmath>
#include <iostream>
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
#endif


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
    pthread_exit(NULL);
}

int main(){
    init();
    pthread_t id;
    int ret = pthread_create(&id,NULL,chkAprilTags,NULL);
    int a = 1;static char buf[2048];
    sendSomething("123");
    recvSomething(buf);
    while(1){
        a++;a--;
    }

    printf("23333");
    return 0;
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

