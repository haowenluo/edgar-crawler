@echo off
REM Batch script to run extraction with Anaconda base environment

echo Activating Anaconda base environment...
call conda activate base

echo.
echo Running year-by-year extraction...
echo.

cd /d "c:\Users\luh\OneDrive - Purdue University Fort Wayne\Documents\edgar-crawler\local processing"
python year_by_year_extraction.py

echo.
echo Extraction complete!
pause


