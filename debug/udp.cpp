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
	//printf("%s\n",buf);

}
int main(){
    char* a;
    init();
    while (scanf("%s",a)==1){
        
        sendSomething(a);
    }
    return 0;
}

