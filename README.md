# Word Multiplier GUI (Python + CustomTkinter)

This project is a GUI simulator for binary **word multiplication** (Shift-and-Add and Booth algorithms)
built with **CustomTkinter** for a modern look. It was created to match the contents of the uploaded PDF "Simulate a Word Multiplier".

## Files
- `src/main.py` - main application
- `requirements.txt` - Python dependencies

## Run (local)
1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/macOS
   venv\\Scripts\\activate     # Windows (PowerShell)
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python src/main.py
   ```

## Using in IntelliJ IDEA Ultimate
1. Open IntelliJ IDEA, choose **Open** and select this project folder.
2. Configure a Python SDK (Project Interpreter) in Settings / Preferences.
3. Run `src/main.py` from the Run configurations.

## Notes
- The GUI uses `customtkinter`. If you prefer classic `tkinter`, edit `src/main.py` accordingly.
- The app supports 4, 8, and 16-bit words. It logs step-by-step operations and lets you export the log.
