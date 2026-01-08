import socket
import time
import pygame

ROBOT_IP = "192.168.137.207"

   # example: "192.168.137.104"
ROBOT_PORT = 4210
ROBOT_ID = 1

SEND_HZ = 30

def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() < 1:
        print("NO CONTROLLER FOUND")
        return

    pad = pygame.joystick.Joystick(0)
    pad.init()

    print("Controller:", pad.get_name())
    print("Sending to:", ROBOT_IP)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dt = 1.0 / SEND_HZ

    while True:
        pygame.event.pump()

        # Xbox X button = button 0
        x_pressed = 1 if pad.get_button(0) else 0

        msg = f"{ROBOT_ID},{x_pressed}\n".encode("utf-8")
        sock.sendto(msg, (ROBOT_IP, ROBOT_PORT))

        print("X BUTTON:", "HELD" if x_pressed else "RELEASED", end="\r")

        time.sleep(dt)

if __name__ == "__main__":
    main()
