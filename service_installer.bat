@ECHO off

:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
    IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
>nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
) ELSE (
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
)


REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
	echo Requesting administrative privileges...
	goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params= %*
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

echo NOTE: There is no error checking, make sure you're inputs are correct.

::Get necessary paths
set cmd='where python'
FOR /F "tokens=*" %%i IN (%cmd%) DO (
	SET python_location=%%i
	goto :pass
	)
:pass
set cmd='cd'
FOR /F "tokens=*" %%i IN (%cmd%) DO SET current_working_directory=%%i
set ms_service_installer=%current_working_directory%\nssm-2.24\win64\nssm.exe
set path_to_manage=%current_working_directory%\TvShuffleForPlex\manage.py

::Get hostname and port from user
set /p host_name=Enter the IP to run the app on:
set /p port_number=Enter the PORT to run the app on:

set path_to_manage_with_args=%path_to_manage% runserver %host_name%:%port_number%

:: Make DB migrations
set cmd=%python_location% %path_to_manage% makemigrations
start %cmd%
set cmd=%python_location% %path_to_manage% migrate
start %cmd%

:: Install the service
set cmd=%ms_service_installer% install TvShuffleForPlex %python_location% %path_to_manage_with_args%
start %cmd%

:: Start the service
set cmd=%ms_service_installer% start TvShuffleForPlex
start %cmd%

echo App service installed, go to 'http://%host_name%:%port_number%/login' in your browser

PAUSE
