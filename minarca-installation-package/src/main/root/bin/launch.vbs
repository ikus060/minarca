Dim scriptArgs
Set scriptArgs = WScript.Arguments
Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & scriptArgs(0) & Chr(34), 0
Set WinScriptHost = Nothing