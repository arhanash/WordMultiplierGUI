# main.py
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import csv
import math
import sys

# Try to import winsound for Windows beep; fallback to simple print('\a')
try:
    import winsound
    def beep(freq=750, dur=60):
        winsound.Beep(freq, dur)
except Exception:
    def beep(freq=750, dur=60):
        # cross-platform attempt; terminal bell as fallback
        try:
            print('\a', end='', flush=True)
        except Exception:
            pass

# Try to import reportlab for PDF export; we'll fallback to TXT otherwise
PDF_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as pdfcanvas
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

# ========== Theme Setup ==========
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ========== Utilities ==========
def int_to_twos_complement(x, bits):
    """Return bits-bit two's complement representation for integer x (works for negative as well)."""
    return format((x + (1 << bits)) % (1 << bits), f"0{bits}b")

def twos_complement_to_int(binstr):
    """Interpret binary string as two's complement signed integer."""
    return int(binstr, 2) - (1 << len(binstr)) if binstr[0] == "1" else int(binstr, 2)

def min_bits_for_signed(a, b):
    """Return minimum bits to represent signed operands a and b (include sign)."""
    max_val = max(abs(a), abs(b))
    if max_val == 0:
        return 2  # allow for sign
    bits = math.ceil(math.log2(max_val + 1)) + 1  # +1 for sign
    # round up to conventional sizes
    if bits <= 8:
        return 8
    if bits <= 16:
        return 16
    return 32

def min_bits_for_unsigned(a, b):
    max_val = max(a, b)
    if max_val == 0:
        return 1
    bits = math.ceil(math.log2(max_val + 1))
    if bits <= 8:
        return 8
    if bits <= 16:
        return 16
    return 32

# ========== Algorithms (pure functions returning steps) ==========
def shift_and_add_steps(A_bin, B_bin, N, signed=False):
    steps = []
    mask = (1 << N) - 1
    A_val = int(A_bin, 2)
    B_val = int(B_bin, 2)
    A_reg = 0
    Q_reg = B_val
    steps.append((0, f"{A_reg:0{N}b}", f"{Q_reg:0{N}b}", "Initialize"))
    for i in range(N):
        if Q_reg & 1:
            A_reg = (A_reg + A_val) & mask
            op = "Add"
        else:
            op = "No Add"
        combined = ((A_reg << N) | Q_reg) >> 1
        A_reg, Q_reg = (combined >> N) & mask, combined & mask
        steps.append((i + 1, f"{A_reg:0{N}b}", f"{Q_reg:0{N}b}", f"{op}, Shift"))
    product_bin = f"{(A_reg << N) | Q_reg:0{2 * N}b}"
    if signed:
        product_val = twos_complement_to_int(product_bin)
    else:
        product_val = int(product_bin, 2)
    return steps, product_bin, product_val

def booth_steps(A_bin, B_bin, N, signed=False):
    steps = []
    mask = (1 << N) - 1
    M = twos_complement_to_int(A_bin)
    Q = twos_complement_to_int(B_bin)
    A = 0
    q_1 = 0
    steps.append((0, f"{A & mask:0{N}b}", f"{Q & mask:0{N}b}", "Initialize"))
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
        # Arithmetic right shift on combined A,Q,q_1
        combined = ((A & mask) << (N + 1)) | ((Q & mask) << 1) | q_1
        # preserve sign in Python manual style: >>1 arithmetic simulated by checking sign of A
        sign = (A >> (N - 1)) & 1
        combined >>= 1
        if sign:
            combined |= (1 << (2 * N))  # keep sign extension if negative
        A = (combined >> (N + 1)) & mask
        Q = (combined >> 1) & mask
        q_1 = combined & 1
        steps.append((step, f"{A:0{N}b}", f"{Q:0{N}b}", f"{op}, Shift"))
    product = (A << N) | Q
    product_bin = f"{product & ((1 << (2 * N)) - 1):0{2 * N}b}"
    if signed:
        product_val = twos_complement_to_int(product_bin)
    else:
        product_val = int(product_bin, 2)
    return steps, product_bin, product_val

# ========== App ==========
class MacStyleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Word Multiplier Simulator by Arhan-Peter-Arjun-Abhinav")
        self.geometry("1200x820")
        self.minsize(1000, 700)

        # fonts
        self.header_font = ("Helvetica Neue", 26, "bold")
        self.label_font = ("Helvetica Neue", 16)
        self.entry_font = ("Helvetica Neue", 18)
        self.mono_font = ("Courier New", 14)

        # model state
        self.operand_a = None
        self.operand_b = None
        self.mode = tk.StringVar(value="unsigned")
        self.compare = tk.BooleanVar(value=True)
        self.auto_mode = tk.BooleanVar(value=True)  # auto vs manual stepping
        self.bits = 8

        # result containers
        self.sa_steps = []
        self.booth_steps = []
        self.sa_product = None
        self.booth_product = None
        self.sa_result = None
        self.booth_result = None

        # build UI
        self._build_header()
        self._build_body()
        self._build_footer()

    # ---------- Header ----------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=("white", "#1c1c1e"), corner_radius=16)
        header.pack(fill="x", pady=(10, 5))

        # Title
        title = ctk.CTkLabel(header, text=" WORD MULTIPLIER SIMULATOR", font=self.header_font)
        title.pack(side="left", padx=20, pady=15)

        # Appearance mode switch
        def toggle_mode():
            current = ctk.get_appearance_mode()
            if current == "Light":
                ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode("light")

        mode_btn = ctk.CTkSwitch(header, text="🌙 Dark Mode", command=toggle_mode)
        mode_btn.pack(side="right", padx=20, pady=15)


    # ---------- Body ----------
    def _build_body(self):
        main = ctk.CTkFrame(self, fg_color=("white", "#f9f9f9"))
        main.pack(fill="both", expand=True, padx=10, pady=6)

        # Left: inputs / controls
        left = ctk.CTkFrame(main, width=320)
        left.pack(side="left", fill="y", padx=(6, 8), pady=6)

        ctk.CTkLabel(left, text="Inputs", font=self.label_font).pack(pady=(12, 6))
        # operand A
        ctk.CTkLabel(left, text="Operand A (decimal):", anchor="w").pack(fill="x", padx=12)
        self.entry_a = ctk.CTkEntry(left, width=260, font=self.entry_font)
        self.entry_a.pack(padx=12, pady=(4, 8))
        self.entry_a.bind("<Return>", lambda e: self.entry_b.focus())

        # operand B
        ctk.CTkLabel(left, text="Operand B (decimal):", anchor="w").pack(fill="x", padx=12)
        self.entry_b = ctk.CTkEntry(left, width=260, font=self.entry_font)
        self.entry_b.pack(padx=12, pady=(4, 12))
        self.entry_b.bind("<Return>", lambda e: self._prepare_and_run())

        # signed/unsigned radio
        ctk.CTkLabel(left, text="Number Mode:", anchor="w").pack(fill="x", padx=12)
        rb_frame = ctk.CTkFrame(left, fg_color="transparent")
        rb_frame.pack(padx=12, pady=8)
        ctk.CTkRadioButton(rb_frame, text="Unsigned", variable=self.mode, value="unsigned").pack(side="left", padx=6)
        ctk.CTkRadioButton(rb_frame, text="Signed", variable=self.mode, value="signed").pack(side="left", padx=6)

        # compare toggle
        ctk.CTkCheckBox(left, text="Compare both algorithms (side-by-side)", variable=self.compare).pack(padx=12, pady=(8, 6))

        # auto/manual toggle
        ctk.CTkCheckBox(left, text="Auto-play steps", variable=self.auto_mode).pack(padx=12, pady=(2, 12))

        # bit-size display & detection button
        self.bits_label = ctk.CTkLabel(left, text="Bit Size: —", font=("Helvetica Neue", 14, "bold"))
        self.bits_label.pack(padx=12, pady=(4, 12))

        detect_btn = ctk.CTkButton(left, text="Detect & Prepare ▶", command=self._prepare_and_run)
        detect_btn.pack(padx=12, pady=(6, 6), fill="x")

        # Export group
        ctk.CTkLabel(left, text="Export Results:", anchor="w").pack(fill="x", padx=12, pady=(16, 4))
        ctk.CTkButton(left, text="Export CSV", command=self._export_csv).pack(padx=12, pady=(4, 4), fill="x")
        ctk.CTkButton(left, text="Export PDF/TXT", command=self._export_pdf_or_txt).pack(padx=12, pady=(4, 16), fill="x")

        # Right: simulation panels
        right = ctk.CTkFrame(main)
        right.pack(side="left", fill="both", expand=True, padx=(8, 6), pady=6)

        # Top summary area
        top_summary = ctk.CTkFrame(right, height=80, fg_color=("transparent"))
        top_summary.pack(fill="x", padx=6, pady=(6, 6))
        self.summary_label = ctk.CTkLabel(top_summary, text="Summary: —", anchor="w", font=("Helvetica Neue", 13))
        self.summary_label.pack(fill="x", padx=6)

        # Middle: two algorithm panes
        panes = ctk.CTkFrame(right)
        panes.pack(fill="both", expand=True, padx=6, pady=6)

        # Shift-and-Add pane
        self.sa_frame = ctk.CTkFrame(panes, fg_color=("#f5f5f7", "#1c1c1e"))
        self.sa_frame.pack(side="left", fill="both", expand=True, padx=(0, 3), pady=6)

        ctk.CTkLabel(self.sa_frame, text="Shift-and-Add", font=("Helvetica Neue", 16, "bold")).pack(pady=(8, 6))
        # treeview
        sa_style = ttk.Style()
        sa_style.configure("SA.Treeview", font=self.mono_font, rowheight=30)
        self.sa_table = ttk.Treeview(self.sa_frame, columns=("Step", "A", "Q", "Operation"), show="headings", height=10, style="SA.Treeview")
        for c in ("Step", "A", "Q", "Operation"):
            self.sa_table.heading(c, text=c)
            self.sa_table.column(c, anchor="center", width=140)
        self.sa_table.pack(fill="both", expand=True, padx=6, pady=6)

        # progress & animation canvas & log
        self.sa_progress = ctk.CTkProgressBar(self.sa_frame)
        self.sa_progress.pack(fill="x", padx=10, pady=(4, 8))
        self.sa_anim_canvas = tk.Canvas(self.sa_frame, height=48)
        self.sa_anim_canvas.pack(fill="x", padx=10, pady=(2, 8))
        self.sa_log = ctk.CTkTextbox(self.sa_frame, height=120, font=self.mono_font)
        self.sa_log.pack(fill="x", padx=10, pady=(6, 10))

        # Booth pane
        self.booth_frame = ctk.CTkFrame(panes, fg_color=("#f5f5f7", "#1c1c1e"))
        self.booth_frame.pack(side="left", fill="both", expand=True, padx=(3, 0), pady=6)

        ctk.CTkLabel(self.booth_frame, text="Booth's Algorithm", font=("Helvetica Neue", 16, "bold")).pack(pady=(8, 6))
        booth_style = ttk.Style()
        booth_style.configure("B.Treeview", font=self.mono_font, rowheight=30)
        self.booth_table = ttk.Treeview(self.booth_frame, columns=("Step", "A", "Q", "Operation"), show="headings", height=10, style="B.Treeview")
        for c in ("Step", "A", "Q", "Operation"):
            self.booth_table.heading(c, text=c)
            self.booth_table.column(c, anchor="center", width=140)
        self.booth_table.pack(fill="both", expand=True, padx=6, pady=6)

        self.booth_progress = ctk.CTkProgressBar(self.booth_frame)
        self.booth_progress.pack(fill="x", padx=10, pady=(4, 8))
        self.booth_anim_canvas = tk.Canvas(self.booth_frame, height=48)
        self.booth_anim_canvas.pack(fill="x", padx=10, pady=(2, 8))
        self.booth_log = ctk.CTkTextbox(self.booth_frame, height=120, font=self.mono_font)
        self.booth_log.pack(fill="x", padx=10, pady=(6, 10))

        # Bottom result summary table
        bottom = ctk.CTkFrame(right)
        bottom.pack(fill="x", padx=6, pady=(6, 10))
        ctk.CTkLabel(bottom, text="Final Summary", font=("Helvetica Neue", 14, "bold")).pack(anchor="w", padx=6, pady=(4, 2))
        self.summary_tree = ttk.Treeview(bottom, columns=("Label", "Binary", "Decimal"), show="headings", height=3)
        for c in ("Label", "Binary", "Decimal"):
            self.summary_tree.heading(c, text=c)
            self.summary_tree.column(c, anchor="center", width=200)
        self.summary_tree.pack(fill="x", padx=6, pady=(4, 8))

    # ---------- Footer ----------
    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color=("transparent"))
        footer.pack(fill="x", padx=6, pady=(2, 8))
        self.run_btn = ctk.CTkButton(footer, text="Run Simulation ▶", width=200, command=self._prepare_and_run)
        self.run_btn.pack(side="left", padx=8)
        self.step_btn = ctk.CTkButton(footer, text="Next Step ►", command=self._manual_next_step)
        self.step_btn.pack(side="left", padx=6)
        self.stop_flag = False
        ctk.CTkLabel(footer, text="Tip: Press Enter in B to start", font=("Helvetica Neue", 11)).pack(side="right", padx=6)

    # ---------- Prepare & Run ----------
    def _prepare_and_run(self, event=None):
        # validate inputs
        a_raw = self.entry_a.get().strip()
        b_raw = self.entry_b.get().strip()
        if not a_raw or not b_raw:
            messagebox.showerror("Input error", "Please enter both operands")
            return
        # allow negative sign if signed mode
        try:
            if self.mode.get() == "signed":
                a = int(a_raw)
                b = int(b_raw)
            else:
                if "-" in a_raw or "-" in b_raw:
                    raise ValueError("Unsigned mode doesn't accept negative")
                a = int(a_raw)
                b = int(b_raw)
            self.operand_a = a
            self.operand_b = b
        except ValueError as e:
            messagebox.showerror("Invalid input", f"Enter valid integers.\n{e}")
            return

        # determine bits
        if self.mode.get() == "signed":
            bits = min_bits_for_signed(self.operand_a, self.operand_b)
        else:
            bits = min_bits_for_unsigned(self.operand_a, self.operand_b)
        self.bits = bits
        self.bits_label.configure(text=f"Bit Size: {bits}-bit")
        # show summary line
        A_bin = int_to_twos_complement(self.operand_a, bits)
        B_bin = int_to_twos_complement(self.operand_b, bits)
        self.summary_label.configure(text=f"A={self.operand_a} ({A_bin})  |  B={self.operand_b} ({B_bin})  | Mode={self.mode.get()}")
        # warnings for overflow / large numbers
        if bits >= 32:
            messagebox.showwarning("Large bit size", "Operands require 32-bit representation; consider smaller inputs for readability.")

        # compute both algorithms if compare enabled, else only chosen? We'll compute both for comparison
        signed_flag = (self.mode.get() == "signed")
        self.sa_steps, self.sa_product, self.sa_result = shift_and_add_steps(A_bin, B_bin, bits, signed=signed_flag)
        self.booth_steps, self.booth_product, self.booth_result = booth_steps(A_bin, B_bin, bits, signed=signed_flag)

        # prepare UI tables and logs
        self._reset_tables_and_logs()
        # if comparison unchecked, hide booth pane visually
        if not self.compare.get():
            self.booth_frame.pack_forget()
        else:
            # ensure both packed
            if not self.booth_frame.winfo_ismapped():
                self.booth_frame.pack(side="left", fill="both", expand=True, padx=(3, 0), pady=6)

        # fill initial rows and start animate (auto or manual)
        if self.auto_mode.get():
            # start threaded animation to keep UI responsive
            self.stop_flag = False
            threading.Thread(target=self._animate_both_auto, daemon=True).start()
        else:
            # manual: show first (initial) rows
            for s in self.sa_steps[:1]:
                self.sa_table.insert("", "end", values=s)
                self.sa_log.insert("end", f"Step {s[0]} | A={s[1]} | Q={s[2]} | {s[3]}\n")
            for s in self.booth_steps[:1]:
                self.booth_table.insert("", "end", values=s)
                self.booth_log.insert("end", f"Step {s[0]} | A={s[1]} | Q={s[2]} | {s[3]}\n")
            self.sa_progress.set(1 / max(len(self.sa_steps), 1))
            self.booth_progress.set(1 / max(len(self.booth_steps), 1))
            # show summary
            self._update_final_summary()

    def _reset_tables_and_logs(self):
        for tbl in (self.sa_table, self.booth_table):
            tbl.delete(*tbl.get_children())
        for log in (self.sa_log, self.booth_log):
            log.delete("1.0", "end")
        # reset progress bars and canvases
        self.sa_progress.set(0)
        self.booth_progress.set(0)
        self.sa_anim_canvas.delete("all")
        self.booth_anim_canvas.delete("all")
        self.summary_tree.delete(*self.summary_tree.get_children())

    # ---------- Animation Helpers ----------
    def _draw_bits_on_canvas(self, canvas: tk.Canvas, binstr: str):
        canvas.delete("all")
        w = canvas.winfo_width() or canvas.winfo_reqwidth()
        # show bits evenly spaced
        spacing = max(10, min(28, w // max(len(binstr), 1)))
        x = 6
        y = 22
        for ch in binstr:
            # draw rectangle and bit
            canvas.create_rectangle(x, 4, x + spacing - 2, 40, outline="#444", width=1, fill="#fff")
            canvas.create_text(x + (spacing - 2) / 2, y, text=ch, font=("Courier", 12))
            x += spacing

    def _animate_both_auto(self):
        # run animation step by step for both algorithms (synchronized by step index)
        total_sa = len(self.sa_steps)
        total_booth = len(self.booth_steps)
        total = max(total_sa, total_booth)
        for i in range(total):
            if self.stop_flag:
                break
            # SAFELY insert row if exists
            if i < total_sa:
                s = self.sa_steps[i]
                self.sa_table.insert("", "end", values=s)
                self.sa_table.see(self.sa_table.get_children()[-1])
                self.sa_log.insert("end", f"Step {s[0]} | A={s[1]} | Q={s[2]} | {s[3]}\n")
                # draw combined A|Q for simple visual
                self._draw_bits_on_canvas(self.sa_anim_canvas, s[1] + " " + s[2])
                self.sa_progress.set((i + 1) / total_sa)
                beep()  # sound feedback
            if i < total_booth:
                b = self.booth_steps[i]
                self.booth_table.insert("", "end", values=b)
                self.booth_table.see(self.booth_table.get_children()[-1])
                self.booth_log.insert("end", f"Step {b[0]} | A={b[1]} | Q={b[2]} | {b[3]}\n")
                self._draw_bits_on_canvas(self.booth_anim_canvas, b[1] + " " + b[2])
                self.booth_progress.set((i + 1) / total_booth)
                beep(880, 45)
            # give a small pause between steps
            time.sleep(0.6)
        # final summary update after both end
        self._update_final_summary()

    # ---------- Manual stepping ----------
    def _manual_next_step(self):
        # This advances one step in manual mode for both tables (if available)
        if self.auto_mode.get():
            messagebox.showinfo("Manual step disabled", "Switch off Auto-play to use manual stepping.")
            return
        # find current counts
        sa_count = len(self.sa_table.get_children())
        booth_count = len(self.booth_table.get_children())
        # insert next if present
        advanced = False
        if sa_count < len(self.sa_steps):
            s = self.sa_steps[sa_count]
            self.sa_table.insert("", "end", values=s)
            self.sa_table.see(self.sa_table.get_children()[-1])
            self.sa_log.insert("end", f"Step {s[0]} | A={s[1]} | Q={s[2]} | {s[3]}\n")
            self._draw_bits_on_canvas(self.sa_anim_canvas, s[1] + " " + s[2])
            self.sa_progress.set((sa_count + 1) / max(1, len(self.sa_steps)))
            beep()
            advanced = True
        if self.compare.get() and (booth_count < len(self.booth_steps)):
            b = self.booth_steps[booth_count]
            self.booth_table.insert("", "end", values=b)
            self.booth_table.see(self.booth_table.get_children()[-1])
            self.booth_log.insert("end", f"Step {b[0]} | A={b[1]} | Q={b[2]} | {b[3]}\n")
            self._draw_bits_on_canvas(self.booth_anim_canvas, b[1] + " " + b[2])
            self.booth_progress.set((booth_count + 1) / max(1, len(self.booth_steps)))
            beep(880, 45)
            advanced = True
        if not advanced:
            messagebox.showinfo("Done", "No more steps to advance.")
            self._update_final_summary()

    # ---------- Final Summary ----------
    def _update_final_summary(self):
        # clear
        self.summary_tree.delete(*self.summary_tree.get_children())
        bits = self.bits
        A_bin = int_to_twos_complement(self.operand_a, bits)
        B_bin = int_to_twos_complement(self.operand_b, bits)
        # choose whichever product to show; if comparing, show both as separate rows
        # Insert A row, B row, SA result row, Booth result row
        self.summary_tree.insert("", "end", values=("A", A_bin, str(self.operand_a)))
        self.summary_tree.insert("", "end", values=("B", B_bin, str(self.operand_b)))
        # SA product
        if self.sa_product is not None:
            self.summary_tree.insert("", "end", values=("ShiftAdd Prod", self.sa_product, str(self.sa_result)))
        if self.booth_product is not None:
            self.summary_tree.insert("", "end", values=("Booth Prod", self.booth_product, str(self.booth_result)))

    # ---------- Exporting ----------
    def _gather_export_rows(self):
        """Prepare rows for CSV export: steps from SA and Booth with headers and summary."""
        rows = []
        rows.append(["Word Multiplier Simulation Export"])
        rows.append(["Operands", f"A={self.operand_a}", f"B={self.operand_b}", f"Mode={self.mode.get()}", f"Bits={self.bits}"])
        rows.append([])
        rows.append(["Shift-and-Add Steps"])
        rows.append(["Step", "A", "Q", "Operation"])
        for s in self.sa_steps:
            rows.append(list(s))
        rows.append([])
        rows.append(["Booth Steps"])
        rows.append(["Step", "A", "Q", "Operation"])
        for b in self.booth_steps:
            rows.append(list(b))
        rows.append([])
        rows.append(["Summary"])
        rows.append(["A (bin)", int_to_twos_complement(self.operand_a, self.bits)])
        rows.append(["B (bin)", int_to_twos_complement(self.operand_b, self.bits)])
        rows.append(["ShiftAdd Product (bin)", self.sa_product or ""])
        rows.append(["ShiftAdd Product (dec)", str(self.sa_result) if self.sa_result is not None else ""])
        rows.append(["Booth Product (bin)", self.booth_product or ""])
        rows.append(["Booth Product (dec)", str(self.booth_result) if self.booth_result is not None else ""])
        return rows

    def _export_csv(self):
        if not self.sa_steps and not self.booth_steps:
            messagebox.showerror("Nothing to export", "Run a simulation first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            rows = self._gather_export_rows()
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo("Exported", f"CSV exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    def _export_pdf_or_txt(self):
        if not self.sa_steps and not self.booth_steps:
            messagebox.showerror("Nothing to export", "Run a simulation first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf" if PDF_AVAILABLE else ".txt",
                                            filetypes=[("PDF", "*.pdf")] if PDF_AVAILABLE else [("Text File", "*.txt")])
        if not path:
            return
        rows = self._gather_export_rows()
        try:
            if PDF_AVAILABLE and path.lower().endswith(".pdf"):
                c = pdfcanvas.Canvas(path, pagesize=letter)
                w, h = letter
                y = h - 40
                text_obj = c.beginText(30, y)
                text_obj.setFont("Courier", 10)
                for r in rows:
                    line = "  ".join([str(x) for x in r])
                    text_obj.textLine(line)
                    y -= 12
                    if y < 40:
                        c.drawText(text_obj)
                        c.showPage()
                        text_obj = c.beginText(30, h - 40)
                        text_obj.setFont("Courier", 10)
                        y = h - 40
                c.drawText(text_obj)
                c.save()
                messagebox.showinfo("Exported", f"PDF saved to:\n{path}")
            else:
                # fallback to plain text
                with open(path, "w") as f:
                    for r in rows:
                        f.write("  ".join([str(x) for x in r]) + "\n")
                messagebox.showinfo("Exported", f"Text saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    # ---------- Graceful exit helpers (optional) ----------
    def on_closing(self):
        self.stop_flag = True
        self.destroy()

# ========== Run App ==========
if __name__ == "__main__":
    app = MacStyleApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
