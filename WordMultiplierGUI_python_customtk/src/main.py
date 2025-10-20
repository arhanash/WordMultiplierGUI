"""
Word Multiplier Simulator (macOS Glass Style)
---------------------------------------------
Modern macOS-like UI with frosted glass effect, rounded corners,
and guided wizard flow for simulation.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

# ========== Theme setup ==========
ctk.set_appearance_mode("light")   # macOS style light theme
ctk.set_default_color_theme("blue")

# ========== Utility ==========
def int_to_twos_complement(x, bits):
    return format((x + (1 << bits)) % (1 << bits), f"0{bits}b")

def twos_complement_to_int(binstr):
    return int(binstr, 2) - (1 << len(binstr)) if binstr[0] == "1" else int(binstr, 2)

# ========== Algorithms ==========
def shift_and_add_steps(A_bin, B_bin, N):
    steps, mask = [], (1 << N) - 1
    A_val, B_val = int(A_bin, 2), int(B_bin, 2)
    A_reg, Q_reg = 0, B_val
    steps.append((0, f"{A_reg:0{N}b}", f"{Q_reg:0{N}b}", "Initialize"))

    for i in range(N):
        if Q_reg & 1:
            A_reg = (A_reg + A_val) & mask
            op = "Add"
        else:
            op = "No Add"
        combined = ((A_reg << N) | Q_reg) >> 1
        A_reg, Q_reg = (combined >> N) & mask, combined & mask
        steps.append((i+1, f"{A_reg:0{N}b}", f"{Q_reg:0{N}b}", f"{op}, Shift"))
    product = f"{(A_reg << N) | Q_reg:0{2*N}b}"
    return steps, product, int(product, 2)

def booth_steps(A_bin, B_bin, N):
    steps = []
    mask = (1 << N) - 1

    M = twos_complement_to_int(A_bin)
    Q = twos_complement_to_int(B_bin)
    A = 0
    q_1 = 0

    steps.append((0, f"{A & mask:0{N}b}", f"{Q & mask:0{N}b}", "Initialization"))

    for step in range(1, N + 1):
        q0 = Q & 1
        if (q0, q_1) == (1, 0):
            A = A - M
            op = "A = A - M"
        elif (q0, q_1) == (0, 1):
            A = A + M
            op = "A = A + M"
        else:
            op = "No operation"

        # Arithmetic right shift
        sign_bit = (A >> (N - 1)) & 1
        combined = ((A & ((1 << N) - 1)) << (N + 1)) | ((Q & mask) << 1) | q_1
        combined >>= 1
        if sign_bit:
            combined |= (1 << (2 * N))
        A = (combined >> (N + 1)) & mask
        Q = (combined >> 1) & mask
        q_1 = combined & 1

        steps.append((step, f"{A:0{N}b}", f"{Q:0{N}b}", f"{op}, Shift"))

    product = (A << N) | Q
    product_bin = f"{product & ((1 << (2 * N)) - 1):0{2 * N}b}"
    result = twos_complement_to_int(product_bin)

    return steps, product_bin, result

# ========== App ==========
class MacStyleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(" Word Multiplier Simulator")
        self.geometry("980x720")
        self.resizable(True, True)

        # Fonts
        self.header_font = ("Helvetica Neue", 26, "bold")
        self.label_font = ("Helvetica Neue", 16)
        self.entry_font = ("Helvetica Neue", 18)

        # Wizard variables
        self.current_step = 0
        self.operand_a = None
        self.operand_b = None
        self.algorithm = None

        # UI setup
        self._build_header()
        self._build_pages()

    # --- Header (Glass style) ---
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=("white", "#f5f5f5"), corner_radius=16)
        header.pack(fill="x", pady=(10, 5))
        title = ctk.CTkLabel(header, text="️ 💕 Word Multiplier Simulator", font=self.header_font, text_color="#222")
        title.pack(pady=15)

    # --- Wizard Pages ---
    def _build_pages(self):
        self.container = ctk.CTkFrame(self, fg_color=("white", "#f9f9f9"), corner_radius=18)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.pages = [
            self._page_operand(1, "Enter first number (A):"),
            self._page_operand(2, "Enter second number (B):"),
            self._page_algorithm(),
            self._page_simulation()
        ]
        for p in self.pages:
            p.pack_forget()
        self.pages[0].pack(fill="both", expand=True)

    def _page_operand(self, step, label_text):
        frame = ctk.CTkFrame(self.container, corner_radius=16, fg_color=("#f5f5f7", "#1c1c1e"))
        ctk.CTkLabel(frame, text=label_text, font=self.label_font, text_color="#111").pack(pady=(40, 10))
        entry = ctk.CTkEntry(frame, width=220, font=self.entry_font, corner_radius=10)
        entry.pack(pady=10)
        ctk.CTkLabel(frame, text="(Enter decimal number)", font=("Helvetica Neue", 13)).pack(pady=10)

        def next_action():
            val = entry.get().strip()
            if not val.isdigit():
                messagebox.showerror("Error", "Enter a valid decimal number.")
                return
            if step == 1:
                self.operand_a = int(val)
            else:
                self.operand_b = int(val)
            self._next_page()

        ctk.CTkButton(frame, text="Next ➜", width=160, height=40, corner_radius=12,
                      fg_color="#007aff", hover_color="#0060d0", text_color="white",
                      font=("Helvetica Neue", 16, "bold"),
                      command=next_action).pack(pady=(20, 40))
        return frame

    def _page_algorithm(self):
        frame = ctk.CTkFrame(self.container, corner_radius=16, fg_color=("#f5f5f7", "#1c1c1e"))
        ctk.CTkLabel(frame, text="Choose Algorithm", font=self.label_font).pack(pady=(40, 10))
        self.alg_box = ctk.CTkComboBox(frame, values=["Shift-and-Add", "Booth"], width=220, font=self.entry_font)
        self.alg_box.set("Shift-and-Add")
        self.alg_box.pack(pady=20)

        self.mode = tk.StringVar(value="unsigned")
        rb_frame = ctk.CTkFrame(frame, fg_color="transparent")
        rb_frame.pack(pady=20)
        ctk.CTkRadioButton(rb_frame, text="Unsigned", variable=self.mode, value="unsigned").pack(side="left", padx=20)
        ctk.CTkRadioButton(rb_frame, text="Signed", variable=self.mode, value="signed").pack(side="left", padx=20)

        ctk.CTkButton(frame, text="Start Simulation ▶", width=200, height=45, corner_radius=12,
                      fg_color="#007aff", hover_color="#0060d0", text_color="white",
                      font=("Helvetica Neue", 16, "bold"),
                      command=self._start_simulation).pack(pady=(30, 40))
        return frame

    def _page_simulation(self):
        frame = ctk.CTkFrame(self.container, corner_radius=16, fg_color=("#f5f5f7", "#1c1c1e"))

        self.table = ttk.Treeview(frame, columns=("Step", "A", "Q", "Operation"), show="headings", height=12)
        for c in ("Step", "A", "Q", "Operation"):
            self.table.heading(c, text=c)
            self.table.column(c, anchor="center", width=180)
        self.table.pack(fill="both", expand=True, pady=20, padx=20)

        self.log = ctk.CTkTextbox(frame, width=850, height=120, font=("Courier New", 14))
        self.log.pack(pady=(10, 20))
        return frame

    # --- Navigation ---
    def _next_page(self):
        self.pages[self.current_step].pack_forget()
        self.current_step += 1
        self.pages[self.current_step].pack(fill="both", expand=True)

    def _start_simulation(self):
        self.algorithm = self.alg_box.get()
        a, b = self.operand_a, self.operand_b
        mode = self.mode.get()
        bits = 8 if max(a, b) < 128 else 16
        A_bin = int_to_twos_complement(a, bits)
        B_bin = int_to_twos_complement(b, bits)

        if self.algorithm == "Shift-and-Add":
            self.steps, product, result = shift_and_add_steps(A_bin, B_bin, bits)
        else:
            self.steps, product, result = booth_steps(A_bin, B_bin, bits)

        self.product, self.result = product, result
        self._next_page()
        self._animate_steps()

    # --- Animation ---
    def _animate_steps(self):
        self.table.delete(*self.table.get_children())
        self.log.delete("1.0", "end")

        def animate(i=0):
            if i >= len(self.steps):
                self.log.insert("end", f"\n\nFinal Product: {self.product}\nDecimal Result: {self.result}")
                return
            s = self.steps[i]
            self.table.insert("", "end", values=s)
            self.table.see(self.table.get_children()[-1])
            self.log.insert("end", f"Step {s[0]} | A={s[1]} | Q={s[2]} | {s[3]}\n")
            self.after(800, lambda: animate(i+1))
        animate()

# ========== Run ==========
if __name__ == "__main__":
    app = MacStyleApp()
    app.mainloop()
