import socket
import time
import tkinter as tk
import pygame

ROBOTS = {
    1: "192.168.137.207",
    2: "192.168.137.208",
    3: "192.168.137.209",
    4: "192.168.137.210",
}
UDP_PORT = 4210

CONTROL_ROBOT_ID = 1

SEND_HZ = 30
SEND_INTERVAL_MS = int(1000 / SEND_HZ)

# If you want to force a specific button later, set this to an int.
# Leave as None to auto-detect.
X_BUTTON_INDEX = None


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Control (UI + Controller)")
        self.root.geometry("1000x620")
        self.root.configure(bg="#0b1220")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.pad = None
        self.x_held = False
        self.x_button_index = X_BUTTON_INDEX  # learned button index (or forced)
        self._last_sent_buttons = None
        self._last_print_state = None

        self._build_ui()
        self._init_controller()

        self.root.after(100, self._tick_controller)
        self.root.after(SEND_INTERVAL_MS, self._tick_send)

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#0b1220")
        header.pack(fill="x", padx=16, pady=16)

        tk.Label(header, text="Robot Control", fg="white", bg="#0b1220",
                 font=("Segoe UI", 22, "bold")).pack(side="left")

        tk.Button(header, text="STOP ALL ROBOTS",
                  bg="#d62828", fg="white", bd=0,
                  activebackground="#b91c1c",
                  font=("Segoe UI", 12, "bold"),
                  padx=18, pady=10,
                  command=self.stop_all).pack(side="right")

        self.status = tk.Label(self.root, text="Controller: (starting...)", fg="#cbd5e1", bg="#0b1220",
                               font=("Segoe UI", 11))
        self.status.pack(anchor="w", padx=16)

        self.learn_label = tk.Label(self.root, text="X mapping: (press your X button once to learn)",
                                    fg="#94a3b8", bg="#0b1220", font=("Segoe UI", 10))
        self.learn_label.pack(anchor="w", padx=16, pady=(2, 0))

        self.x_label = tk.Label(self.root, text="X: RELEASED", fg="#cbd5e1", bg="#0b1220",
                                font=("Segoe UI", 12, "bold"))
        self.x_label.pack(anchor="w", padx=16, pady=(6, 12))

        grid = tk.Frame(self.root, bg="#0b1220")
        grid.pack(fill="both", expand=True, padx=16, pady=8)

        def make_card(rid):
            card = tk.Frame(grid, bg="#121a2b", highlightthickness=1, highlightbackground="#22304f")
            tk.Label(card, text=f"Robot {rid}", fg="white", bg="#121a2b",
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
            tk.Label(card, text=f"IP: {ROBOTS[rid]}", fg="#94a3b8", bg="#121a2b",
                     font=("Segoe UI", 10)).pack(anchor="w", padx=12)

            tk.Button(card, text="STOP", bg="#d62828", fg="white", bd=0,
                      activebackground="#b91c1c",
                      font=("Segoe UI", 11, "bold"),
                      padx=14, pady=10,
                      command=lambda r=rid: self.send_buttons(r, 0)).pack(anchor="e", padx=12, pady=12)
            return card

        cards = [make_card(1), make_card(2), make_card(3), make_card(4)]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for card, (r, c) in zip(cards, positions):
            card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")

        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        footer_text = f"Controller controls Robot {CONTROL_ROBOT_ID} | Sends: robotId,1 while held; robotId,0 when released"
        tk.Label(self.root, text=footer_text, fg="#94a3b8", bg="#0b1220", font=("Segoe UI", 10))\
            .pack(anchor="w", padx=16, pady=(0, 12))

    def _init_controller(self):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() < 1:
            self.status.config(text="Controller: NOT FOUND (plug it in)")
            self.pad = None
            return

        self.pad = pygame.joystick.Joystick(0)
        self.pad.init()
        self.status.config(text=f"Controller: {self.pad.get_name()} (OK)")

        if self.x_button_index is not None:
            self.learn_label.config(text=f"X mapping: button index {self.x_button_index} (forced)")

    def send_buttons(self, rid, buttons):
        ip = ROBOTS.get(rid)
        if not ip:
            return
        msg = f"{rid},{buttons}\n".encode("utf-8")
        self.sock.sendto(msg, (ip, UDP_PORT))

        # Print only when the value changes (no spam)
        state = (rid, buttons)
        if state != self._last_print_state:
            print(f"SEND -> {rid},{buttons}  to {ip}:{UDP_PORT}")
            self._last_print_state = state

    def stop_all(self):
        for rid in ROBOTS.keys():
            self.send_buttons(rid, 0)

    def _learn_x_button_if_needed(self):
        # If we haven't learned X yet, learn the first pressed button
        if self.x_button_index is not None or self.pad is None:
            return

        n = self.pad.get_numbuttons()
        for i in range(n):
            if self.pad.get_button(i):
                self.x_button_index = i
                self.learn_label.config(text=f"X mapping: learned button index {i}")
                print(f"LEARNED X BUTTON INDEX: {i}")
                break

    def _tick_controller(self):
        if self.pad is None:
            self._init_controller()
            self.root.after(500, self._tick_controller)
            return

        pygame.event.pump()

        # Auto-learn mapping if needed
        self._learn_x_button_if_needed()

        # Read X state
        x_now = False
        if self.x_button_index is not None:
            try:
                x_now = bool(self.pad.get_button(self.x_button_index))
            except Exception:
                x_now = False

        if x_now != self.x_held:
            self.x_held = x_now
            self.x_label.config(text="X: HELD" if self.x_held else "X: RELEASED")

        self.root.after(20, self._tick_controller)

    def _tick_send(self):
        rid = CONTROL_ROBOT_ID
        buttons = 1 if self.x_held else 0
        self.send_buttons(rid, buttons)
        self.root.after(SEND_INTERVAL_MS, self._tick_send)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
