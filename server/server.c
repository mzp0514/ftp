#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>
#include <pthread.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <memory.h>
#include <stdio.h>
#include <regex.h>


#define STATEMENT_BUFFER_SIZE 512
#define DIR_BUFFER_SIZE 128
#define FILE_TRANSFER_BUFFER_SIZE 8192
char base_dir[DIR_BUFFER_SIZE];


struct Service {

    int id;
    int pasv;
    int cmd_fd;
    int dt_fd;

    int dt_pasv_fd;
    int dt_cn_fd;

    int authc1;
    int authc2;

	long cur_pos;

	char old_path[DIR_BUFFER_SIZE];
    char working_dir[DIR_BUFFER_SIZE];

	char transferring_file_dir[DIR_BUFFER_SIZE];

};


struct Service* createService(int ccf, int id){
    struct Service* service = malloc(sizeof(struct Service));
	service->cmd_fd = ccf;
    service->dt_fd = -1;
    service->id = id;
    service->authc2 = 0;
    service->authc1 = 0;
    service->pasv = 0;
	service->cur_pos = 0;
	service->working_dir[0] = 0;
	return service;
}


void estDtConn(struct Service* service, struct sockaddr_in sock_addr){
	if ((service->dt_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        exit(0);
    }

    if (connect(service->dt_fd, (struct sockaddr *) &sock_addr, sizeof(sock_addr)) < 0) {
        return;
    }
}


void clsDtConn(struct Service* service){
	if (service->dt_fd == -1) return;
    close(service->dt_fd);
    if (service->pasv) {
        close(service->dt_pasv_fd);
        close(service->dt_cn_fd);
    }
}


int prcIP(char* sentence, int* ip, int* port){
    char* rem;
    *ip = atoi(strtok_r(sentence, ",", &rem)) << 24;
	for(int i = 2; i >= 0; i--){
		*ip += atoi(strtok_r(NULL , ",", &rem)) << (i * 8);
	}
	*port = 0;
	for(int i = 1; i >= 0; i--){
		*port += atoi(strtok_r(NULL , ",", &rem)) << (i * 8);
	}

	return 1;
}


int execCmd(struct Service* service, char* command){
	usleep(10000);
    char* rem;
	char* cmd = strtok_r(command, " ", &rem);
	char* cntnt = strtok_r(NULL, " ", &rem);
	if(strcmp(cmd, "RNTO")){
		service->old_path[0] = '\0';
	}

    if (strcmp(cmd, "USER") && strcmp(cmd, "PASS") && !service->authc2) {
		char* str = "500 Permission denied\r\n";
		send(service->cmd_fd, str, strlen(str), 0);
        return -1;
    }
    
	if(strcmp(cmd, "USER") == 0){
		if (strcmp(cntnt, "anonymous") == 0) {
            char* str = "331 Guest login ok, send your complete e-mail address as password\r\n";
		    send(service->cmd_fd, str, strlen(str), 0);
			service->authc1 = 1;
        } else {
            char* str = "500 All users other than anonymous are not supported\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
        }
	}

	else if(strcmp(cmd, "PASS") == 0){
		if (!service->authc1) {
			char* str = "500 Permission denied\r\n";
		    send(service->cmd_fd, str, strlen(str), 0);
			
		}
		else{
			char* str1 = "230 Welcome to School of Software\r\n";
 		    send(service->cmd_fd, str1, strlen(str1), 0);
            service->authc2 = 1;
			// if(!cntnt){
            //     char* str1 = "230 Welcome to School of Software\r\n";
 		    //     send(service->cmd_fd, str1, strlen(str1), 0);
            //     service->authc2 = 1;
			// }
			// else{
            //     int status, i;
            //     int flag = REG_EXTENDED;
            //     regmatch_t pmatch[1];
            //     const size_t nmatch=1;
            //     regex_t reg;
                
            //     regcomp(&reg, "^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\\.[a-zA-Z0-9_-]+)+$", flag);
                
            //     status = regexec(&reg, cntnt, nmatch, pmatch, 0);
                
            //     regfree(&reg);
                
			// 	if(status == 0){
			// 		char* str1 = "230 Welcome to School of Software\r\n";
 		    //         send(service->cmd_fd, str1, strlen(str1), 0);
            //         service->authc2 = 1;
			// 	}
			// 	else{
			// 		char* str1 = "500 password error\r\n";
 		    //         send(service->cmd_fd, str1, strlen(str1), 0);
			// 	}
			// }
		}
	}
	
	else if(strcmp(cmd, "SYST") == 0){
		char* str = "215 UNIX Type: L8\r\n";
		send(service->cmd_fd, str, strlen(str), 0);
	} 

	else if (strcmp(cmd, "TYPE") == 0) {
        if(strcmp(cntnt, "I") == 0 ){
            char* str = "200 Type set to I.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
		}
		else{
			char* str = "500 Permission denied.\r\n";
		    send(service->cmd_fd, str, strlen(str), 0);
		}
				
	}

	else if(strcmp(cmd, "QUIT") == 0 || strcmp(cmd, "ABOR") == 0){
		char* str = "221 goodbye\r\n";
		send(service->cmd_fd, str, strlen(str), 0);
		return -1;
	}

	else if(strcmp(cmd, "PORT") == 0){
		service->pasv = 0;
	
		int port = 0, ip = 0;
		
		if(prcIP(cntnt, &ip, &port)){
            struct sockaddr_in port_addr;

            memset(&port_addr, 0, sizeof(port_addr));
            port_addr.sin_family = AF_INET;
            port_addr.sin_port = htons(port);
            port_addr.sin_addr.s_addr = htonl(ip);
            estDtConn(service, port_addr);

            char* str = "200 PORT command successful.\r\n";	
			send(service->cmd_fd, str, strlen(str), 0);
		}
		else{
			char* str = "500 Permission denied\r\n";
		    send(service->cmd_fd, str, strlen(str), 0);
		}
	}

	else if(strcmp(cmd, "PASV") == 0){
		service->pasv = 1;

        service->dt_pasv_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);

        struct sockaddr_in pasv_addr;
        memset(&pasv_addr, 0, sizeof(pasv_addr));

        pasv_addr.sin_family = AF_INET;
        pasv_addr.sin_addr.s_addr = htonl(INADDR_ANY);

        unsigned short pasv_port;

        while (1) {
            pasv_port = (unsigned short)(rand() % 45535 + 20000);
            pasv_addr.sin_port = htons(pasv_port);
            if (bind(service->dt_pasv_fd, (struct sockaddr *) &pasv_addr, sizeof(pasv_addr)) >= 0)
                break;
        }

        char respStr[50];
        sprintf(respStr, "227 Entering PassiveMode (127,0,0,1,%d,%d)\r\n", (pasv_port >> 8) & 0xFF, pasv_port & 0xFF);
        send(service->cmd_fd, respStr, strlen(respStr), 0);

        listen(service->dt_pasv_fd, 10);
        service->dt_cn_fd = accept(service->dt_pasv_fd, (struct sockaddr *) NULL, NULL);
         
	}
	else if(strcmp(cmd, "REST") == 0){
        service->cur_pos = atol(cntnt);
		char* str = "350 set start point successfully.\r\n";
		send(service->cmd_fd, str, strlen(str), 0);
	}

	else if(strcmp(cmd, "RETR") == 0){
		int valid = 1;
		for(int i = 0; i < strlen(cntnt); i++){
			if(cntnt[i] == '/' ){
                valid = 0;
				break;
			}
		}
		if(!valid){
			char* str = "550 Not accessible.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
			return -1;
		}
        
		char dir[STATEMENT_BUFFER_SIZE];

		if(service->transferring_file_dir[0] == 0){
		    sprintf(dir, "%s%s/%s", base_dir, service->working_dir, cntnt);
		}
		else{
            strcpy(dir, service->transferring_file_dir);
		}

		FILE* f = fopen(dir, "rb");

		printf("RETR dir: %s\r\n", dir);

		if(!f) {
			char* str = "451 No such file or directory.\r\n";
			printf("%s\r\n", str);
			send(service->cmd_fd, str, strlen(str), 0);
			clsDtConn(service);
		}
        else {
            int real_fd = service->pasv ? service->dt_cn_fd : service->dt_fd;

            fseek(f, 0, SEEK_END);
			long f_size = ftell(f);
			fseek(f, service->cur_pos, SEEK_SET);
            
			printf("st pos: %ld\r\n", service->cur_pos);
			char str[STATEMENT_BUFFER_SIZE];
			sprintf(str, "150 Opening BINARY mode data connection for %s (%ld bytes). \r\n", cntnt, f_size);
            send(service->cmd_fd, str, strlen(str), 0);
            
            char file_buf[FILE_TRANSFER_BUFFER_SIZE];
			long i = service->cur_pos;
	        while(!feof(f)) {
		        int l = fread(file_buf, sizeof(char), FILE_TRANSFER_BUFFER_SIZE - 1, f);
				file_buf[l] = '\0';
				i += (long) l;
		        int u = send(real_fd, file_buf, l, 0);
				
				usleep(100);
				if(u <= 0){
					printf("break\r\n");
					break;
				}
	        }

			fclose(f);
            clsDtConn(service);

			if(i == f_size){
			    sleep(1);
			    service->cur_pos = 0;
				service->transferring_file_dir[0] = 0;
			    char* str2 = "226 Transfer complete.\r\n";
                send(service->cmd_fd, str2, strlen(str2), 0);
			}

			else{
				strcpy(service->transferring_file_dir, dir);
			}
			
        } 
	}

	else if(strcmp(cmd, "STOR") == 0){
		int valid = 1;
		for(int i = 0; i < strlen(cntnt); i++){
			if(cntnt[i] == '/'){
                valid = 0;
				break;
			}
		}
		if(!valid){
			char* str = "550 Not accessible.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
		}

		char dir[STATEMENT_BUFFER_SIZE];
		sprintf(dir, "%s%s/%s", base_dir, service->working_dir, cntnt);
        FILE* f = fopen(dir, "wb");
		printf("STOR dir: %s\r\n", dir);

		if(!f) {
			char* str = "451 Error creating file.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
			clsDtConn(service);
		}
        else {
            int real_fd = service->pasv ? service->dt_cn_fd : service->dt_fd;
            char file_buf[FILE_TRANSFER_BUFFER_SIZE];
            
			char str[STATEMENT_BUFFER_SIZE];
			sprintf(str, "150 Opening BINARY mode data connection for %s\r\n", cntnt);
            send(service->cmd_fd, str, strlen(str), 0);
			
            int l = 0;
            while (1) {
                l = recv(real_fd, file_buf, FILE_TRANSFER_BUFFER_SIZE - 1, 0);
				if( l <= 0){
					break;
				}
                file_buf[l] = '\0';
				
                fwrite(file_buf, sizeof(char), l, f);
            } 
            clsDtConn(service);
			fclose(f);
            
			sleep(1);

			char* str2 = "226 Transfer complete.\r\n";
            send(service->cmd_fd, str2, strlen(str2), 0);
        } 
	}

	else if(strcmp(cmd, "LIST") == 0){
		char command[STATEMENT_BUFFER_SIZE];

        if(cntnt){
			if(cntnt[0] == '/'){
                sprintf(command, "ls %s%s -l", base_dir, cntnt);
			}
			else{
                sprintf(command, "ls %s%s/%s -l", base_dir, service->working_dir, cntnt);
			}
		}
		else{
			sprintf(command, "ls %s%s -l", base_dir, service->working_dir);
		}

		FILE *fstream = popen(command, "r");
        char buff[FILE_TRANSFER_BUFFER_SIZE];
        memset(buff, 0, sizeof(char) * FILE_TRANSFER_BUFFER_SIZE);
        fread(buff, FILE_TRANSFER_BUFFER_SIZE, 1, fstream);
        pclose(fstream);
        
		int real_fd = service->pasv ? service->dt_cn_fd : service->dt_fd;
        char* str2 = "150 Here comes the directory listing.\r\n";
		send(service->cmd_fd, str2, strlen(str2), 0);

        char* remn;
	    strtok_r(buff, "\r\n", &remn);
	    
		send(real_fd, remn, strlen(remn), 0);
        usleep(10000);

		char* str = "226 send list successfully.\r\n";
        send(service->cmd_fd, str, strlen(str), 0);
        
        clsDtConn(service);
        
	}

	else if(strcmp(cmd, "PWD") == 0){
		printf("%s\r\n", service->working_dir);
		char str[STATEMENT_BUFFER_SIZE];
		sprintf(str, "257 \"%s\" is the current directory.\r\n", service->working_dir);
		send(service->cmd_fd, str, strlen(str), 0);
	}

	else if(strcmp(cmd, "CWD") == 0){
		printf("%s\r\n", cntnt);
          
        if (cntnt[0] == '/') {
			strcpy(service->working_dir, cntnt);
		}
        else {
            char req[STATEMENT_BUFFER_SIZE];
			strcpy(req, cntnt);
            if (req[strlen(req) - 1] == '/') {
				req[strlen(req) - 1] = 0;
			}
            while (strlen(req) != 0) {
				int len = strlen(req);
				printf("len of req: %d\r\n", len);
                if (strlen(req) >= 2 && req[0] == '.' && req[1] == '.') {
					if(len == 2){
                        req[0] = 0;
					}
                    else if(len >= 3){
					    for(int i = 3; i < len; i++){
						    req[i - 3] = req[i];
					    }
					    req[len - 3] = 0;
					}

					int wd_len = strlen(service->working_dir);

                    if (wd_len <= 0) {
						char* str = "550 Not accessible.\r\n";
			            send(service->cmd_fd, str, strlen(str), 0);
						return 0;
					}
					
					for(int i = wd_len - 1; i >= 0; i--){
						if(service->working_dir[i] == '/'){
							
							service->working_dir[i] = 0;
							break;
						}
					}

                } 
				else if (req[0] == '.') {
                    for(int i = 2; i < len; i++){
						req[i - 2] = req[i];
					}
					req[len - 2] = 0;
                } 
				else {
					int wd_len = strlen(service->working_dir);
                    for(int i = 0; i < len; i++){
						service->working_dir[wd_len + i] = req[i];
					}
					service->working_dir[wd_len + len] = 0;
                    req[0] = 0;
                }
            }

        }

		char str[STATEMENT_BUFFER_SIZE];
		sprintf(str, "250 \"%s\" is the current directory.\r\n", service->working_dir);
		send(service->cmd_fd, str, strlen(str), 0);
	}

	else if(strcmp(cmd, "RMD") == 0){
        char command[STATEMENT_BUFFER_SIZE];
		if(cntnt){
			if(cntnt[0] == '/'){
                sprintf(command, "%s%s", base_dir, cntnt);
			}
			else{
                sprintf(command, "%s%s/%s", base_dir, service->working_dir, cntnt);
			}
		}
		else{
			char* str = "502 command error.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
			return 0;
		}
		    
		if(rmdir(command) == 0){
		    char str[STATEMENT_BUFFER_SIZE];
		    sprintf(str, "257 \"%s%s/%s\" removed\r\n", base_dir, service->working_dir, cntnt);
            send(service->cmd_fd, str, strlen(str), 0);
		}
		else{
			char str[] = "550 rmdir failed\r\n";
            send(service->cmd_fd, str, strlen(str), 0);
		}


	}

	else if(strcmp(cmd, "MKD") == 0){
        char command[STATEMENT_BUFFER_SIZE];
		if(cntnt){
			if(cntnt[0] == '/'){
                sprintf(command, "%s%s", base_dir, cntnt);
			}
			else{
                sprintf(command, "%s%s/%s", base_dir, service->working_dir, cntnt);
			}
		}
		else {
			char* str = "502 command error.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
			return 0;
		}
		    
		if(mkdir(command,  0777) == 0){
		    char str[STATEMENT_BUFFER_SIZE];
		    sprintf(str, "257 \"%s/%s\" created\r\n", service->working_dir, cntnt);
            send(service->cmd_fd, str, strlen(str), 0);
		}
		else{
			char str[] = "550 mkdir failed\r\n";
            send(service->cmd_fd, str, strlen(str), 0);
		}
	}

	else if(strcmp(cmd, "RNFR") == 0){
		char command[STATEMENT_BUFFER_SIZE];
        if(cntnt){
			if(cntnt[0] == '/'){
                sprintf(command, "%s%s", base_dir, cntnt);
			}
			else{
                sprintf(command, "%s%s/%s", base_dir, service->working_dir, cntnt);
			}
		}
		else {
			char* str = "502 command error.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
			return 0;
		}
		
		struct stat path_stat;
        if(stat(command, &path_stat) == 0){
            char* str = "350 Please send target name\r\n";
            send(service->cmd_fd, str, strlen(str), 0);
			strcpy(service->old_path, command);
		}
		else{
            char* str = "550 RNFR Failed\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
		}
	}

	else if(strcmp(cmd, "RNTO") == 0){
        char command[STATEMENT_BUFFER_SIZE];
        if(cntnt){
			if(cntnt[0] == '/'){
                sprintf(command, "%s%s", base_dir, cntnt);
			}
			else{
                sprintf(command, "%s%s/%s", base_dir, service->working_dir, cntnt);
			}
		}
		else {
			char* str = "502 command error.\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
			service->old_path[0] = '\0';
			return 0;
		}
		if(service->old_path[0] == '\0'){
			char* str = "550 Please specify target name\r\n";
			send(service->cmd_fd, str, strlen(str), 0);
		}
		else{
			if(rename(service->old_path, command) == 0){
                char* str = "250 Rename successfully\r\n";
                send(service->cmd_fd, str, strlen(str), 0);
			}
			else{
				char* str = "550 RNTO Failed\r\n";
			    send(service->cmd_fd, str, strlen(str), 0);
			}
		}
        service->old_path[0] = '\0';
	}
    
    return 0;
}


void* startService(void* arg){

	struct Service* service = (struct Service*) arg;

    service->authc2 = 0;
    service->authc1 = 0;
    
    char* str1 = "220 FTP server ready.\r\n";
	send(service->cmd_fd, str1, strlen(str1), 0);
    
    while (1) {
        int n;
        char buffer[STATEMENT_BUFFER_SIZE];
		char* p;
        n = recv(service->cmd_fd, buffer, STATEMENT_BUFFER_SIZE - 1, 0);
        buffer[n] = 0;

        char* cmd = strtok_r(buffer, "\r\n", &p);

        int res = execCmd(service, cmd);

        if (res != 0) {
            close(service->cmd_fd);
            break;
        }

    }

}


int main(int argc, char **argv) {
	int listenfd;		
	struct sockaddr_in addr;
	int p;
	int len;
	int cnt = 0;

	if ((listenfd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == -1) {
		printf("Error socket(): %s(%d)\n", strerror(errno), errno);
		return 1;
	}

	int port = 21;

    if(argc == 1){
		strcpy(base_dir, "/tmp");
	}
	else if(argc == 3){
        if(strcmp(argv[1], "-port") == 0){
            port = atoi(argv[2]);
			strcpy(base_dir, "/tmp");
		}
		else if(strcmp(argv[1], "-root") == 0){
            strcpy(base_dir, argv[2]);
		}
		else{
			printf("invalid arguments");
			return 0;
		}
	}
	else if(argc == 5){
        if(strcmp(argv[1], "-port") == 0 && strcmp(argv[3], "-root") == 0){
			port = atoi(argv[2]);
			strcpy(base_dir, argv[4]);
		}
		else if(strcmp(argv[3], "-port") == 0 && strcmp(argv[1], "-root") == 0){
			port = atoi(argv[4]);
			strcpy(base_dir, argv[2]);
		}
		else{
			printf("invalid arguments");
			return 0;
		}
	}
	else {
		printf("invalid arguments");
			return 0;
	}

	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_port = htons(port);
	addr.sin_addr.s_addr = htonl(INADDR_ANY);	


	if (bind(listenfd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
		printf("Error bind(): %s(%d)\n", strerror(errno), errno);
		return 1;
	}

	if (listen(listenfd, 10) == -1) {
		printf("Error listen(): %s(%d)\n", strerror(errno), errno);
		return 1;
	}
	
	while (1) {
		int connfd = 0;

		if ((connfd = accept(listenfd, NULL, NULL)) == -1) {
			printf("Error accept(): %s(%d)\n", strerror(errno), errno);
			continue;
		} 
    
        struct Service* instance = createService(connfd, cnt++);
        pthread_t t;
		pthread_create(&t, NULL, startService, (void*) instance);

        if (cnt == 100) break;

	}

	close(listenfd);
	return 0;
}

