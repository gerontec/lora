#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <termios.h>

#define TIMEOUT 500 // milliseconds

void send_command(int fd, const char *cmd) {
    char buffer[256];
    snprintf(buffer, sizeof(buffer), "%s\r\n", cmd);
    printf("Sending command: %s\n", cmd);
    write(fd, buffer, strlen(buffer));
    usleep(100000);  // Wartezeit für die Antwort
    int n = read(fd, buffer, sizeof(buffer));
    if (n > 0) {
        buffer[n] = '\0';
        printf("Response: %s\n", buffer);
    } else {
        printf("No response received\n");
    }
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <device>\n", argv[0]);
        return 1;
    }

    const char *device = argv[1];  // Gerät aus dem Kommandozeilenargument
    int serial_fd = open(device, O_RDWR | O_NOCTTY | O_SYNC);
    if (serial_fd < 0) {
        perror("Error opening serial port");
        return 1;
    }

    struct termios tty;
    if (tcgetattr(serial_fd, &tty) != 0) {
        perror("Error from tcgetattr");
        close(serial_fd);
        return 1;
    }

    cfsetospeed(&tty, B9600);
    cfsetispeed(&tty, B9600);

    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;  // 8-bit chars
    tty.c_iflag &= ~IGNBRK;  // disable break processing
    tty.c_lflag = 0;  // no signaling chars, no echo,
                      // no canonical processing
    tty.c_oflag = 0;  // no remapping, no delays
    tty.c_cc[VMIN]  = 0;  // read doesn't block
    tty.c_cc[VTIME] = 5;  // 0.5 seconds read timeout

    tty.c_iflag &= ~(IXON | IXOFF | IXANY);  // shut off xon/xoff ctrl

    tty.c_cflag |= (CLOCAL | CREAD);  // ignore modem controls,
                                      // enable reading
    tty.c_cflag &= ~(PARENB | PARODD);  // shut off parity
    tty.c_cflag |= 0;
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CRTSCTS;

    if (tcsetattr(serial_fd, TCSANOW, &tty) != 0) {
        perror("Error from tcsetattr");
        close(serial_fd);
        return 1;
    }

    // Initial setup commands
    send_command(serial_fd, "mac set nwkskey 00000000000000000000000000000000");  // Network session key (example)
    send_command(serial_fd, "mac set appskey 00000000000000000000000000000000");  // Application session key (example)
    send_command(serial_fd, "mac join abp");  // Join network

    // Main loop
    while (1) {
        // Example: Send a message
        send_command(serial_fd, "mac tx cnf 1 010203");  // Confirmed message with payload 010203

        // Example: Setup for receiving
        send_command(serial_fd, "mac rx 1");

        // Sleep for a while before sending the next message
        sleep(10);  // Sleep for 10 seconds
    }

    // Close the serial port
    close(serial_fd);
    return 0;
}