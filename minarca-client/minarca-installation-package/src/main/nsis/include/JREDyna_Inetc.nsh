; Version 1.0.0

  !ifndef JRE_DECLARES
  !define JRE_DECLARES

  !include "WordFunc.nsh"

  !macro CUSTOM_PAGE_JREINFO
    Page custom CUSTOM_PAGE_JREINFO
  !macroend

  !ifndef JRE_VERSION
    !error "JRE_VERSION must be defined"
  !endif

  !ifndef JRE_URL
    !error "JRE_URL must be defined"
  !endif
  
  !ifndef JRE_URL_64
    !error "JRE_URL_64 must be defined"
  !endif

;--------------------------------
;Language Strings
!macro JREINFO_LANGUAGE
  LangString JRE_NOT_FOUND_TITLE ${LANG_ENGLISH} "JRE Installation or Update Required"
  LangString JRE_NOT_FOUND_TITLE ${LANG_FRENCH} "Installation ou mise à jour requise de JRE"
  LangString JRE_NOT_FOUND_SUBTITLE ${LANG_ENGLISH} "This application requires Java ${JRE_VERSION} or higher."
  LangString JRE_NOT_FOUND_SUBTITLE ${LANG_FRENCH} "Cette application nécessite Java ${JRE_VERSION} ou supérieur."
  LangString JRE_NOT_FOUND_LABEL ${LANG_ENGLISH} "This application requires installation of the JRE. This will be downloaded and installed as part of the installation."
  LangString JRE_NOT_FOUND_LABEL ${LANG_FRENCH} "Cette application nécessite l'installation de Java Runtime Environment (JRE). Il sera téléchargé et installé lors de cette installation."
  
  LangString JRE_NOT_FOUND ${LANG_ENGLISH} "No JRE Found"
  LangString JRE_NOT_FOUND ${LANG_FRENCH} "Aucun JRE trouvé"
  LangString JRE_OLD_FOUND ${LANG_ENGLISH} "Old JRE found"
  LangString JRE_OLD_FOUND ${LANG_FRENCH} "Veille version de JRE trouvé"
  LangString JRE_FOUND ${LANG_ENGLISH} "JRE found"
  LangString JRE_FOUND ${LANG_FRENCH} "JRE trouvé"
  LangString JRE_LAUNCH_SETUP ${LANG_ENGLISH} "Launching JRE setup"
  LangString JRE_LAUNCH_SETUP ${LANG_FRENCH} "Lancement de l'installation de JRE"
  LangString JRE_SETUP_COMPLETE ${LANG_ENGLISH} "JRE Setup finished"
  LangString JRE_SETUP_COMPLETE ${LANG_FRENCH} "Installation de JRE terminée"
  LangString JRE_DOWNLOAD ${LANG_ENGLISH} "About to download JRE from "
  LangString JRE_DOWNLOAD ${LANG_FRENCH} "Téléchargement de JRE à partir de "
  LangString JRE_DETECT_VERSION ${LANG_ENGLISH} "Detecting JRE Version"
  LangString JRE_DETECT_VERSION ${LANG_FRENCH} "Détection de la version de JRE"
!macroend

;--------------------------------  
;  Custom panel
Function CUSTOM_PAGE_JREINFO

  push $0
  push $1
  push $2
  
  ; Check if JRE is detected
  Push "${JRE_VERSION}"
  Call DetectJRE
  Pop $0
  Pop $1
  StrCmp $0 "OK" exit

  nsDialogs::create /NOUNLOAD 1018
  pop $1

  StrCmp $0 "0" NoFound
  StrCmp $0 "-1" FoundOld

NoFound:
FoundOld:
  !insertmacro MUI_HEADER_TEXT $(JRE_NOT_FOUND_TITLE) $(JRE_NOT_FOUND_SUBTITLE)
  ${NSD_CreateLabel} 0 0 100% 100% $(JRE_NOT_FOUND_LABEL)
  pop $1
  goto ShowDialog

ShowDialog:

  nsDialogs::Show

exit:

  pop $2
  pop $1
  pop $0

FunctionEnd

;--------------------------------
; Checks to ensure that the installed version of the JRE (if any) is at least that of
; the JRE_VERSION variable.  The JRE will be downloaded and installed if necessary
; The full path of java.exe will be returned on the stack

Function DownloadAndInstallJREIfNecessary

  Push $0
  Push $1

  DetailPrint $(JRE_DETECT_VERSION)
  Push "${JRE_VERSION}"
  Call DetectJRE
  Pop $0    ; Get return value from stack
  Pop $1    ; get JRE path (or error message)
  DetailPrint "JRE Version detection complete... $1"

  strcmp $0 "OK" End downloadJRE

downloadJRE:

  ${If} ${RunningX64}
    DetailPrint "$(JRE_DOWNLOAD) ${JRE_URL_64}"
    Inetc::get "${JRE_URL_64}" "$TEMP\jre_Setup.exe" /END
  ${Else}
    DetailPrint "$(JRE_DOWNLOAD) ${JRE_URL}"
    Inetc::get "${JRE_URL}" "$TEMP\jre_Setup.exe" /END
  ${EndIf}
  Pop $0 # return value = exit code, "OK" if OK
  DetailPrint "Download result = $0"

  strcmp $0 "OK" downloadsuccessful
  MessageBox MB_OK "There was a problem downloading required component - Error: $0" /SD IDOK
  abort
  
downloadsuccessful:

  DetailPrint $(JRE_LAUNCH_SETUP)
  ExecWait '"$TEMP\jre_setup.exe" /s REBOOT=Disable AUTO_UPDATE=0 WEB_JAVA=0 WEB_ANALYTICS=0 /L \"$TEMP\jre_setup.log\"' $0
  goto jreSetupfinished
  
jreSetupFinished:

  DetailPrint $(JRE_SETUP_COMPLETE)
  Delete "$TEMP\jre_setup.exe"
  StrCmp $0 "0" InstallVerif 0
  Push "The JRE setup has been abnormally interrupted - return code $0"
  Goto ExitInstallJRE
 
InstallVerif:

  DetailPrint "Checking the JRE Setup's outcome"
  Push "${JRE_VERSION}"
  Call DetectJRE  
  Pop $0      ; DetectJRE's return value
  Pop $1      ; JRE home (or error message if compatible JRE could not be found)
  StrCmp $0 "OK" 0 JavaVerStillWrong
  Goto JREPathStorage
  
JavaVerStillWrong:

  Push "Unable to find JRE with version above ${JRE_VERSION}, even though the JRE setup was successful$\n$\n$1"
  Goto ExitInstallJRE
 
JREPathStorage:

  push $0   ; => rv, r1, r0
  exch 2    ; => r0, r1, rv
  exch      ; => r1, r0, rv
  Goto End
 
ExitInstallJRE:

  Pop $1
  MessageBox MB_OK "Unable to install Java - Setup will be aborted$\n$\n$1" /SD IDOK
  Pop $1    ; Restore $1
  Pop $0    ; Restore $0
  Abort
  
End:

  Pop $1    ; Restore $1
  Pop $0    ; Restore $0

FunctionEnd

;--------------------------------
; DetectJRE
; Inputs:  Minimum JRE version requested on stack (this value will be overwritten)
; Outputs: Returns two values on the stack: 
;     First value (rv0):  0 - JRE not found. -1 - JRE found but too old. OK - JRE found and meets version criteria
;     Second value (rv1):  Problem description.  Otherwise - Path to the java runtime (javaw.exe will be at .\bin\java.exe relative to this path)
Function DetectJRE

  Exch $0   ; Get version requested  
            ; Now the previous value of $0 is on the stack, and the asked for version of JDK is in $0
  Push $1   ; $1 = Java version string (ie 1.5.0)
  Push $2   ; $2 = Javahome
  Push $3   ; $3 = holds the version comparison result

  ; stack is now:  r3, r2, r1, r0
  ; first, check for an installed JRE
  ReadRegStr $1 HKLM "SOFTWARE\JavaSoft\Java Runtime Environment" "CurrentVersion"
  StrCmp $1 "" DetectTry2
  ReadRegStr $2 HKLM "SOFTWARE\JavaSoft\Java Runtime Environment\$1" "JavaHome"
  StrCmp $2 "" DetectTry2
  Goto GetJRE
 
DetectTry2:

  ; next, check for an installed JDK
  ReadRegStr $1 HKLM "SOFTWARE\JavaSoft\Java Development Kit" "CurrentVersion"
  StrCmp $1 "" NoFound
  ReadRegStr $2 HKLM "SOFTWARE\JavaSoft\Java Development Kit\$1" "JavaHome"
  StrCmp $2 "" NoFound
 
GetJRE:
  ; ok, we found a JRE, let's compare it's version and make sure it is new enough
  ; $0 = version requested. $1 = version found. $2 = javaHome
  IfFileExists "$2\bin\java.exe" 0 NoFound

  ${VersionCompare} $0 $1 $3 ; $3 now contains the result of the comparison
  DetailPrint "Comparing version $0 to $1 results in $3"
  intcmp $3 1 FoundOld
  goto FoundNew
 
NoFound:

  ; No JRE found
  strcpy $0 "0"
  strcpy $1 $(JRE_NOT_FOUND)
  Goto DetectJREEnd
 
FoundOld:

  ; An old JRE was found
  strcpy $0 "-1"
  strcpy $1 $(JRE_OLD_FOUND)
  Goto DetectJREEnd
  
FoundNew:

  ; A suitable JRE was found 
  strcpy $0 "OK"
  strcpy $1 $2
  Goto DetectJREEnd

DetectJREEnd:

  ; at this stage, $0 contains rv0, $1 contains rv1
  ; now, straighten the stack out and recover original values for r0, r1, r2 and r3
  ; there are two return values: rv0 = -1, 0, OK and rv1 = JRE path or problem description
  ; stack looks like this: 
  ;    r3,r2,r1,r0
  Pop $3  ; => r2,r1,r0
  Pop $2  ; => r1,r0
  Push $0 ; => rv0, r1, r0
  Exch 2  ; => r0, r1, rv0
  Push $1 ; => rv1, r0, r1, rv0
  Exch 2  ; => r1, r0, rv1, rv0
  Pop $1  ; => r0, rv1, rv0
  Pop $0  ; => rv1, rv0  
  Exch    ; => rv0, rv1


FunctionEnd

  !endif ; // JRE_DECLARES