# WordMultiplierGUI

A **desktop simulator for binary multiplication** built with **Python, Tkinter, and CustomTkinter**, featuring **Shift-and-Add** and **Booth’s algorithm**. This GUI project allows users to visualize each step of the multiplication process, see intermediate binary registers, and export simulation logs.

---

## 🔹 Features

- **Mac-style GUI** with light and dark mode toggle.
- Supports **signed and unsigned numbers**.
- Step-by-step simulation of two multiplication algorithms:
    - **Shift-and-Add**
    - **Booth's Algorithm**
- Shows **binary registers (A, Q)** at each step in a table.
- **Animated simulation** for easy understanding of the multiplication process.
- **Export simulation log** to CSV or Excel.
- Adaptive **bit size** depending on input number (`8-bit` or `16-bit`).

---

## 🖥️ Screenshots

![WordMultiplierGUI Screenshot](https://github.com/arhanash/WordMultiplierGUI/blob/main/wordmultiplierguiscreenshot.png)

---

## ⚙️ Installation

1. Clone the repository:
```bash
git clone https://github.com/arhanash/WordMultiplierGUI.git
cd WordMultiplierGUI
```
2. Install dependencies:
```bash
pip install customtkinter==6.6.1 pandas==2.1.1 openpyxl==3.1.3
```
3. Run the application:
```bash
python src/main.py
```

---
## 💻 How to Use

1. Enter **first number (A)** in decimal.
2. Enter **second number (B)** in decimal.
3. Choose **algorithm**: `Shift-and-Add` or `Booth`.
4. Choose **mode**: `Signed` or `Unsigned`.
5. Click **Start Simulation** to visualize steps.
6. View **Step Table** and **Log Box**.
7. Export simulation log using the **Export Log** button.
---
## 🧮 Algorithms

### 1. Shift-and-Add
- Simulates classic binary multiplication.
- Adds multiplicand to accumulator if least significant bit of multiplier is 1.
- Shifts registers to the right each step.

### 2. Booth’s Algorithm
- Efficient multiplication using two’s complement.
- Reduces the number of additions/subtractions.
- Handles negative numbers seamlessly.

---

## 🎨 Features in GUI
- Mac-style header with title and dark mode toggle.
- Responsive design with adaptive step table size.
- Animated updates for each multiplication step.
- Export functionality for saving logs to `.csv` or `.xlsx`.

---

## 📝 Dependencies
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [Pandas](https://pandas.pydata.org/) (for log export)
- [OpenPyXL](https://openpyxl.readthedocs.io/) (for Excel export)

> Note: Tkinter is built into the Python standard library.

---

## ✅ Future Improvements
- Support larger bit sizes automatically.
- Add interactive visualizations for each shift/add operation.
- Include real-time error detection for invalid inputs.
- Add unit tests for algorithms.
---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---