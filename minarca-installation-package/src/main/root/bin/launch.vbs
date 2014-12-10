Option Explicit

' Return current working directory (where the script is running).
Function cwd()
	Dim oShell, strPath, oFSO, oFile
	Set oShell = CreateObject("Wscript.Shell")
	strPath = Wscript.ScriptFullName
	Set oFSO = CreateObject("Scripting.FileSystemObject")
	Set oFile = oFSO.GetFile(strPath)
	cwd = oFSO.GetParentFolderName(oFSO.GetParentFolderName(oFile))
	cwd = "C:\Program Files\minarca\"
End Function

' Execute a command line
Function exec(command)
	Call log("INFO", "running: " + command)
	Dim oShell, oExec
	Set oShell = CreateObject("Wscript.Shell")
	oShell.CurrentDirectory = "C:/"
	Set oExec = oShell.Exec(command)
	Do While oExec.Status = 0
		Wscript.sleep 10
	Loop
	exec = oExec.StdOut.ReadAll() + oExec.StdErr.ReadAll()
End Function

' Check if file exists.
Function exists(filename)
	Dim oFSO
	Set oFSO = CreateObject("Scripting.FileSystemObject")
	exists = oFSO.FileExists(filename)
End Function

' Get value of an environment variable.
Function expand(name)
	Dim oShell
	Set oShell = CreateObject("WScript.Shell")
	expand = oShell.ExpandEnvironmentStrings(name)
End Function

' Log a message
Function log(strLevel, strMessage)
    ' Validate the file exits before attempting to write, create if it does not
	Dim strLogFile
	strLogFile = expand("%TEMP%") + "/minarca.log"
	On Error Resume Next
	Call logunsafe("[" + cstr(now()) + "] [" + strLevel + "] " + strMessage, strLogFile)
	On Error GoTo 0
End Function

Function logunsafe(strLine, strFileName)
	Dim oFSO, oFile
	' Write the log into the file
	Set oFSO = CreateObject("Scripting.FileSystemObject")
	WScript.Echo(strLine)
	Set oFile = oFSO.OpentextFile(strFileName, 8, True) 
	oFile.WriteLine(strLine)
	Set oFSO = Nothing
	Set oFile = Nothing
End Function

Function logExec(command)
	Call log("INFO", "running: " + command)
	Dim oShell, oExec
	Set oShell = CreateObject("Wscript.Shell")
	oShell.CurrentDirectory = "C:/"
	Set oExec = oShell.Exec("cmd /S /C """ &  command  & """ 2>&1")
	Do While oExec.Status = 0
		'log("hello3")
	    If Not oExec.StdOut.AtEndOfStream Then
			Call log("EXEC", oExec.StdOut.ReadLine())
		End If
	Loop
End Function

Call log("INFO", "minarca starting")

'Declare constants
Dim MINARCA_CONF_DIR,CONF_FILE,INCLUDES_FILE,EXCLUDES_FILE,USER_PPK,RDIFF_BACKUP_VERSION
Dim RDIFF_BACKUP,PLINK
MINARCA_CONF_DIR=expand("%LOCALAPPDATA%") + "\minarca\"
CONF_FILE=MINARCA_CONF_DIR + "conf"
INCLUDES_FILE=MINARCA_CONF_DIR + "includes"
EXCLUDES_FILE=MINARCA_CONF_DIR + "excludes"
USER_PPK=MINARCA_CONF_DIR + "key.ppk"
RDIFF_BACKUP_VERSION="rdiff-backup 1.2.8"
RDIFF_BACKUP=cwd() + "rdiff-backup-1.2.8\rdiff-backup.exe"
PLINK=cwd() + "putty-0.63\plink.exe"

' Configuration variables
Dim REMOTE_HOST, USERNAME, COMPUTER
' Read configuration file
Call log("INFO", "read config " + CONF_FILE)
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
Call log("INFO", "check configuration")
If Not exists(RDIFF_BACKUP) Then
	Call log("ERROR", "rdiffbackup is missing: " + RDIFF_BACKUP)
	WScript.Quit 1
End If
If Not exists(PLINK) Then
	Call log("ERROR", "plink is missing: " + PLINK)
	WScript.Quit 1
End If
If Not exists(USER_PPK) Then
	Call log("ERROR", "ppk file is missing: " + USER_PPK)
	WScript.Quit 1
End If
If Len(Trim(REMOTE_HOST)) = 0 Then
	Call log("ERROR", "configuration doesn't define the remote host - please reconfigure minarca.")
	WScript.Quit 1
End If
Call log("INFO", "remote-host: " + REMOTE_HOST)
If Len(Trim(USERNAME)) = 0 Then
	Call log("ERROR", "configuration doesn't define a username - please reconfigure minarca.")
	WScript.Quit 1
End If
Call log("INFO", "username: " + USERNAME)
If Len(Trim(COMPUTER)) = 0 Then
	Call log("ERROR", "configuration doesn't define a computer - please reconfigure minarca.")
	WScript.Quit 1
End If
Call log("INFO", "computer: " + COMPUTER)

' CHECK RDIFF-BACKUP VERSION
Call log("INFO", "check remote host connectivity")
Dim strRdiffBackupVersion
strRdiffBackupVersion = exec(PLINK & " -batch -i """ & USER_PPK & """ " & USERNAME & "@" & REMOTE_HOST & " rdiff-backup --version")
Call log("INFO", "check remote rdiff-backup version")
If InStr(RDIFF_BACKUP_VERSION, strRdiffBackupVersion) > 0 Then
	Call log("INFO", "remote host connectivity error:")
	Call log("INFO", strRdiffBackupVersion)
	WScript.Quit 1
End If
Call log("INFO", strRdiffBackupVersion)

Call log("INFO", "start backup")
Dim CMDS
CMDS = """" + RDIFF_BACKUP + """"
CMDS = CMDS + " -v 5 --no-hard-links --exclude-symbolic-links --no-acls"
CMDS = CMDS + " --remote-schema """ + PLINK + " -batch -i " + USER_PPK + " %s rdiff-backup --server"""
CMDS = CMDS + " --exclude-globbing-filelist """ + EXCLUDES_FILE + """"
CMDS = CMDS + " --include-globbing-filelist """ + INCLUDES_FILE + """"
CMDS = CMDS + " --exclude ""C:/**"""
CMDS = CMDS + " ""C:/"""
CMDS = CMDS + " """ + USERNAME + "@" + REMOTE_HOST + "::/home/ikus060/backup/" + COMPUTER + """"
logexec(CMDS)
Call log("INFO", "backup completed")