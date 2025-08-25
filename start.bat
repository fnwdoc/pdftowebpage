@echo off
echo ==================================================
echo  pdftowebpage Application Starter
echo ==================================================
echo.

REM Check if virtual environment exists, if not, create it.
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/update dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

REM Run the Flask application
echo.
echo ==================================================
echo  Starting the Flask server...
echo  Access the application at http://127.0.0.1:5000
echo ==================================================
echo.
start "" http://127.0.0.1:5000
python app.py

echo.
echo Server stopped.
pause
