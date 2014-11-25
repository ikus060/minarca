@echo off
SET _OLDCD="%CD%"
call :redirect >>%TEMP%\minarca.log 2>&1
cd %_OLDCD%
exit /b

:log    - function to log message with dates
SET _LEVEL=%~1
ECHO [%date% %time%][%_LEVEL%] %~2
GOTO:EOF

:redirect
SETLOCAL EnableDelayedExpansion
CALL :log INFO "minarca starting"
REM SETS CONSTANTS
SET _MINARCA_CONF_DIR=%LOCALAPPDATA%\minarca\
SET _CONF_FILE=%_MINARCA_CONF_DIR%conf
SET _INCLUDES_FILE=%_MINARCA_CONF_DIR%includes
SET _EXCLUDES_FILE=%_MINARCA_CONF_DIR%excludes
SET _USER_PPK=%_MINARCA_CONF_DIR%key.ppk
SET _RDIFF_BACKUP_VERSION=rdiff-backup 1.2.8
REM SETS VARIABLES
FOR %%i IN ("%~dp0..\") DO SET _MINARCA=%%~dpi
SET _RDIFF_BACKUP=%_MINARCA%rdiff-backup-1.2.8\rdiff-backup.exe
SET _PLINK=%_MINARCA%putty-0.63\plink.exe

for /f "tokens=1,2 delims==" %%A in (%_CONF_FILE%) do (
CALL :log DEBUG "read config %%A=%%B"
if %%A==remotehost set _REMOTE_HOST="%%~B"
if %%A==username set _USERNAME="%%~B"
if %%A==computername set _COMPUTER="%%~B"
)

REM CHECK CONFIGURATION
CALL :log DEBUG "check configuration"
IF NOT EXIST "%_RDIFF_BACKUP%" (
    CALL :log WARN "rdiffbackup is missing: %_RDIFF_BACKUP%"
	EXIT /b 100
)
IF NOT EXIST "%_PLINK%" (
    CALL :log WARN "rdiffbackup is missing: %_PLINK%"
	EXIT /b 100
)
IF NOT EXIST "%_USER_PPK%" (
	CALL :log WARN "ppk file %_USER_PPK% doesn't exists - please reconfigure minarca."
	EXIT /b 100
)
IF "[%_REMOTE_HOST%]" == "[]" (
	CALL :log WARN "configuration doesn't define the remote host - please reconfigure minarca."
	EXIT /b 101
)
CALL :log TRACE "remote-host: %_REMOTE_HOST%"
IF "[%_USERNAME%]" == "[]" (
	CALL :log WARN "configuration doesn't define a username - please reconfigure minarca."
	EXIT /b 101
)
CALL :log TRACE "username: %_USERNAME%"
IF "[%_COMPUTER%]" == "[]" (
	CALL :log WARN "configuration doesn't define a computer name - please reconfigure minarca."
	EXIT /b 101
)
CALL :log TRACE "computer: %_COMPUTER%"

REM CHECK RDIFF-BACKUP VERSION
CALL :log DEBUG "check remote host connectivity"
"%_PLINK%" -batch -i "%_USER_PPK%" "%_USERNAME%@%_REMOTE_HOST%" rdiff-backup --version > %TEMP%\rdiff-backup-version.tmp 2>&1
FINDSTR /C:"host key is not cached in the registry" %TEMP%\rdiff-backup-version.tmp > NUL
If %ERRORLEVEL% EQU 0 (
  REM REGISTER HOST KEY
  CALL :log DEBUG "accept remote host key"
  ECHO y | "%_PLINK%" -i "%_USER_PPK%" "%_USERNAME%@%_REMOTE_HOST%" rdiff-backup --version > %TEMP%\rdiff-backup-version.tmp 2>&1
)
CALL :log INFO "check remote rdiff-backup version"
FINDSTR /C:"%_RDIFF_BACKUP_VERSION%" %TEMP%\rdiff-backup-version.tmp > NUL
If NOT %ERRORLEVEL% EQU 0 (
  REM UNKNONW VERSION OR CONNECTION ERROR
  SET /p _DATA=<%TEMP%\rdiff-backup-version.tmp
  CALL :log ERROR "remote host connectivity error:"
  CALL :log ERROR "%_DATA%"
)
SET /p _DATA=<%TEMP%\rdiff-backup-version.tmp
CALL :log INFO "%_DATA%"
REM DELETE TEMP FILE
DEL %TEMP%\rdiff-backup-version.tmp

REM BUILD EXCLUDE ARGS
SET _ARGS=
SET _ARGS=%_ARGS% --exclude-globbing-filelist "%_EXCLUDES_FILE%"
SET _ARGS=%_ARGS% --include-globbing-filelist "%_INCLUDES_FILE%"

REM EXCLUDE EVERYTHING ELSE
SET _ARGS=%_ARGS% --exclude "C:/**"

REM EXECUTE BACKUP
CALL :log DEBUG "start backup"
cd C:\
SET PYTHONIOENCODING=UTF-8
@echo on
"%_RDIFF_BACKUP%" --no-hard-links --exclude-symbolic-links --no-acls ^
  --remote-schema "%_PLINK% -batch -i %_USER_PPK% %%s rdiff-backup --server" ^
  %_ARGS% ^
  "C:/" ^
  "%_USERNAME%@%_REMOTE_HOST%::/home/ikus060/backup/%_COMPUTER%"
@echo off
CALL :log DEBUG "backup completed"
exit /b
