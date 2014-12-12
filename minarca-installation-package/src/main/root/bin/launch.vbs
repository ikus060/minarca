Option Explicit

' By default windows will show a window when running this script with wscript,
' because we are using exec(). To avoid displaying command line windows to
' the user, we need to run the process with hidden window.
If Right(LCase(WScript.FullName), 11) <> "cscript.exe" Then
	Dim oShell, returnCode
	Set oShell = CreateObject("WScript.Shell")
	returnCode = oShell.Run("cscript.exe //B //nologo """ & WScript.ScriptFullName & """ -ok", 0, true)
	Set oShell = Nothing
	WScript.Quit returnCode
End If

' Return current working directory (where the script is running).
Function Cwd()
	Dim oShell, strPath, oFSO, oFile
	Set oShell = CreateObject("Wscript.Shell")
	strPath = Wscript.ScriptFullName
	Set oFSO = CreateObject("Scripting.FileSystemObject")
	Set oFile = oFSO.GetFile(strPath)
	Cwd = oFSO.GetParentFolderName(oFSO.GetParentFolderName(oFile)) & "\"
End Function

' Execute a command line
Function Exec(command)
	Call Log("INFO", "running: " + command)
	Dim oShell, oExec
	Set oShell = CreateObject("Wscript.Shell")
	oShell.CurrentDirectory = "C:/"
	Set oExec = oShell.Exec("cmd /S /C """ &  command  & """ 2>&1")
	Do While oExec.Status = 0
		Wscript.sleep 10
	Loop
	Exec = oExec.StdOut.ReadAll() + oExec.StdErr.ReadAll()
End Function

Function ExecPlink(command)
	ExecPlink = Exec("""" & PLINK & """ -batch -i """ & USER_PPK & """ " & USERNAME & "@" & REMOTE_HOST & " " + command)
End Function

' Get value of an environment variable.
Function Expand(name)
	Dim oShell
	Set oShell = CreateObject("WScript.Shell")
	Expand = oShell.ExpandEnvironmentStrings(name)
End Function

' Used to format a date to a string. This implementation was inspired by
' java Formatter.
' %H
Function FormatDate(format, d)
	format = Replace(format, "%Y", Right(Year(d), 4))
    format = Replace(format, "%m", LPad(Month(d), 2, "0"))
    format = Replace(format, "%d", LPad(Day(d), 2, "0"))
    format = Replace(format, "%H", LPad(Hour(d), 2, "0"))
    format = Replace(format, "%M", LPad(Minute(d), 2, "0"))
    format = Replace(format, "%S", LPad(Second(d),2, "0"))
	FormatDate = format
End Function

' Return the configuration directory of minarca.
Function GetConfigDir()
	Dim arrDirs, strDir
	' For WinXP & Win7
	arrDirs = Array(Expand("%PROGRAMDATA%") & "\minarca\", _
					Expand("%ALLUSERSPROFILE%") & "\Application Data\minarca\")
	For Each strDir In arrDirs
		Call Log("DEBUG", "check if config diretory [" & strDir & "] exists")
		If IsDir(strDir) Then
			GetConfigDir = strDir
			Exit For
		End If
	Next
End Function

Function GetLastBackup()
	' Get string similar to .../current_mirror.2014-12-10T08:33:40-05:00.data
	Dim strCurrentMirror
	strCurrentMirror = ExecPlink("ls /home/" + USERNAME + "/backup/" + COMPUTER + "/rdiff-backup-data/current_mirror.*.data")
	'Parse the string
	Dim re
	Set re = New RegExp
	re.Pattern = ".*([0-9]+)-([0-9]+)-([0-9]+)T([0-9]+):([0-9]+):([0-9]+)-([0-9]+):00.data"
	re.IgnoreCase = True
	re.Global = True
	re.MultiLine = False
	'Apply regEx
	Dim m
	Set m = re.Execute(strCurrentMirror)
	If m.Count > 0 Then
		Dim year, month, day, hour, minute
		year = m.Item(0).SubMatches(0)
		month = m.Item(0).SubMatches(1)
		day = m.Item(0).SubMatches(2)
		hour = m.Item(0).SubMatches(3)
		minute = m.Item(0).SubMatches(4)
		Dim lastDate, lastTime
		lastDate = DateSerial(year,month,day)
		lastDate = lastDate + TimeSerial(hour, minute, 0)
		GetLastBackup = lastDate
	Else
		GetLastBackup = DateSerial(1970, 1, 1)
	End If
End Function

'Get TMEP directory
Function GetTempDir()
    ' Get TEMP from SYSTEM
	Dim oShell, oEnv
	Set oShell = CreateObject("WScript.Shell")
	Set oEnv = oShell.Environment("SYSTEM")
	GetTempDir = Expand(oEnv("TEMP"))
End Function

' Check if file exists.
Function IsFile(filename)
	Dim oFSO
	Set oFSO = CreateObject("Scripting.FileSystemObject")
	IsFile = oFSO.FileExists(filename)
End Function

' Check if folder exists.
Function IsDir(filename)
	Dim oFSO
	Set oFSO = CreateObject("Scripting.FileSystemObject")
	IsDir = oFSO.FolderExists(filename)
End Function

' Log a message
Function Log(strLevel, strMessage)
    ' Validate the file exits before attempting to write, create if it does not
	Dim strDate, strLogFile
	' Create date 2014-12-10T13:47:04.545
	strDate = FormatDate("%Y-%m-%dT%H:%M:%S", Now())
	strLogFile = GetTempDir() & "/minarca.log"
	On Error Resume Next
	Call LogUnsafe("[" + strDate + "][" + strLevel + "] " + strMessage, strLogFile)
	On Error GoTo 0
End Function

Function LogUnsafe(strLine, strFileName)
	Dim oFSO, oFile
	' Write the log into the file
	Set oFSO = CreateObject("Scripting.FileSystemObject")
	WScript.Echo(strLine)
	Set oFile = oFSO.OpentextFile(strFileName, 8, True) 
	oFile.WriteLine(strLine)
	Set oFSO = Nothing
	Set oFile = Nothing
End Function

' Log all the environment variable for debugging purpose.
Function LogEnvironmentVariables()
	Dim oShell, env, strItem, arrEnvs, strEnv
	Set oShell = CreateObject("WScript.Shell")
	arrEnvs = Array("PROCESS", "SYSTEM", "USER")
	For Each strEnv In arrEnvs
		Call Log("DEBUG", " " & strEnv)
		Set env = oShell.Environment(strEnv)
		For Each strItem In env
			Call Log("DEBUG", "   " & strItem)
		Next
	Next
End Function

Function LogExec(command)
	Call Log("INFO", "running: " + command)
	Dim oShell, oExec
	Set oShell = CreateObject("Wscript.Shell")
	oShell.CurrentDirectory = "C:/"
	Set oExec = oShell.Exec("cmd /S /C """ &  command  & """ 2>&1")
	Do While oExec.Status = 0
		'log("hello3")
	    If Not oExec.StdOut.AtEndOfStream Then
			Call Log("EXEC", oExec.StdOut.ReadLine())
		End If
	Loop
End Function

' Left pad a string
Function LPad(strValue, length, padChar)
  Dim n : n = 0
  If length > Len(strValue) Then n = length - Len(strValue)
  LPad = String(n, padChar) & strValue
End Function

' Script starting !
Call Log("INFO", "minarca starting")

' For debug purpose, print environment variable
Call LogEnvironmentVariables()

'Declare constants
Dim MINARCA_CONF_DIR,CONF_FILE,INCLUDES_FILE,EXCLUDES_FILE,USER_PPK,RDIFF_BACKUP_VERSION
Dim RDIFF_BACKUP,PLINK
MINARCA_CONF_DIR=GetConfigDir()
CONF_FILE=MINARCA_CONF_DIR + "conf"
INCLUDES_FILE=MINARCA_CONF_DIR + "includes"
EXCLUDES_FILE=MINARCA_CONF_DIR + "excludes"
USER_PPK=MINARCA_CONF_DIR + "key.ppk"
RDIFF_BACKUP_VERSION="rdiff-backup 1.2.8"
RDIFF_BACKUP=Cwd() + "rdiff-backup-1.2.8\rdiff-backup.exe"
PLINK=Cwd() + "putty-0.63\plink.exe"

' Configuration variables
Dim REMOTE_HOST, USERNAME, COMPUTER
' Read configuration file
Call Log("INFO", "read config " + CONF_FILE)
If Not IsFile(CONF_FILE) Then
	Call Log("ERROR", "config file is missing: " + CONF_FILE)
	WScript.Quit 1
End If
Dim oFSO, oFile
Set oFSO = CreateObject("Scripting.FileSystemObject")
Set oFile = oFSO.OpenTextFile(CONF_FILE)
Do Until oFile.AtEndOfStream
	Dim strLine, aParts
	strLine = oFile.ReadLine
	aParts = Split(strLine, "=", 2)
	If IsArray(aParts) And UBound(aParts) > 0 Then
		If aParts(0) = "remotehost" Then
			REMOTE_HOST=aParts(1)
		ElseIf aParts(0) = "username" Then
			USERNAME=aParts(1)
		ElseIf aParts(0) = "computername" Then
			COMPUTER=aParts(1)
		End If
	End If
Loop
oFile.Close

' CHECK CONFIGURATION
Call Log("INFO", "check configuration")
If Not IsFile(RDIFF_BACKUP) Then
	Call Log("ERROR", "rdiffbackup is missing: " + RDIFF_BACKUP)
	WScript.Quit 1
End If
If Not IsFile(PLINK) Then
	Call Log("ERROR", "plink is missing: " + PLINK)
	WScript.Quit 1
End If
If Not IsFile(USER_PPK) Then
	Call Log("ERROR", "ppk file is missing: " + USER_PPK)
	WScript.Quit 1
End If
If Len(Trim(REMOTE_HOST)) = 0 Then
	Call Log("ERROR", "configuration doesn't define the remote host - please reconfigure minarca.")
	WScript.Quit 1
End If
Call Log("INFO", "remote-host: " + REMOTE_HOST)
If Len(Trim(USERNAME)) = 0 Then
	Call Log("ERROR", "configuration doesn't define a username - please reconfigure minarca.")
	WScript.Quit 1
End If
Call Log("INFO", "username: " + USERNAME)
If Len(Trim(COMPUTER)) = 0 Then
	Call Log("ERROR", "configuration doesn't define a computer - please reconfigure minarca.")
	WScript.Quit 1
End If
Call Log("INFO", "computer: " + COMPUTER)

' CHECK RDIFF-BACKUP VERSION
Call Log("INFO", "check remote host connectivity")
Dim strRdiffBackupVersion
strRdiffBackupVersion = ExecPlink("rdiff-backup --version")
Call Log("INFO", "check remote rdiff-backup version")
If InStr(RDIFF_BACKUP_VERSION, strRdiffBackupVersion) > 0 Then
	Call Log("INFO", "remote host connectivity error:")
	Call Log("INFO", strRdiffBackupVersion)
	WScript.Quit 1
End If
Call Log("INFO", strRdiffBackupVersion)

' Check last backup date
Dim lastBackup
lastBackup = GetLastBackup()
Call Log("INFO", "Last backup: " + cstr(lastBackup))
If DateDiff("h", lastBackup, Now()) < 12 Then
	Call Log("INFO", "backup not required")
	WScript.Quit 0
End If

' Run the backup
Call Log("INFO", "start backup")
Dim CMDS
CMDS = """" + RDIFF_BACKUP + """"
CMDS = CMDS + " -v 5 --no-hard-links --exclude-symbolic-links --no-acls"
CMDS = CMDS + " --remote-schema """ + PLINK + " -batch -i " + USER_PPK + " %s rdiff-backup --server"""
CMDS = CMDS + " --exclude-globbing-filelist """ + EXCLUDES_FILE + """"
CMDS = CMDS + " --include-globbing-filelist """ + INCLUDES_FILE + """"
CMDS = CMDS + " --exclude ""C:/**"""
CMDS = CMDS + " ""C:/"""
CMDS = CMDS + " """ + USERNAME + "@" + REMOTE_HOST + "::/home/" + USERNAME + "/backup/" + COMPUTER + """"
LogExec(CMDS)
Call Log("INFO", "backup completed")