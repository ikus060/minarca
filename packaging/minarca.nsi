; Minarca client
;
; Copyright (C) 2025 IKUS Software. All rights reserved.
; IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
; Use is subject to license terms.
;
; This script is used by NSIS to build a Windows installer for Minarca Client.
;

; Displayed to the user
!define AppName "Minarca"
; Used for paths
!define ShortName "minarca"
!define Vendor "Ikus Soft inc."
!define AppExeFile "minarcaw.exe"

; The following should be overide by pyinstaller script.
;!define AppVersion "1.1.1.1"
;!define OutFile "minarca-installer-dev.exe"

; Constant values
!define CFG_FILENAME "setup.cfg"

;--------------------------------
;Includes

Unicode True
SetCompressor bzip2

!include "MUI2.nsh"
!include "Sections.nsh"
!include "x64.nsh"
!include "WinMessages.nsh"
!include "LogicLib.nsh"
!include "StrFunc.nsh"
!include "TextFunc.nsh"

!insertmacro ConfigRead

;--------------------------------
;Configuration
 
  ;General
  VIProductVersion "${AppVersion}"
  VIAddVersionKey "ProductName" "${AppName}"
  VIAddVersionKey "Comments" "Automatically saves your data online for easy access at any time while travelling or in case of equipment loss or breakage."
  VIAddVersionKey "CompanyName" "${Vendor}"
  VIAddVersionKey "LegalCopyright" "© ${Vendor}"
  VIAddVersionKey "FileDescription" "${AppName} ${AppVersion} Installer"
  VIAddVersionKey "FileVersion" "${AppVersion}"
  OutFile "${OutFile}"
  
  ; Define icon
  !define DEFAULT_FAVICON "_internal\minarca_client\ui\theme\resources\favicon.ico"
  !define MUI_ICON "${SPECPATH}\setup.ico"
  !define MUI_UNICON "${SPECPATH}\setup.ico"
 
  ;Folder selection page
  InstallDir "$PROGRAMFILES64\Minarca"
 
  ;Get install folder from registry if available
  InstallDirRegKey HKLM "SOFTWARE\${Vendor}\${ShortName}" ""
 
  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin
  
;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

  ;Show all languages, despite user's codepage
  !define MUI_LANGDLL_ALLLANGUAGES

;--------------------------------
;Language Selection Dialog Settings

  ;Remember the installer language
  !define MUI_LANGDLL_REGISTRY_ROOT "HKCU" 
  !define MUI_LANGDLL_REGISTRY_KEY "SOFTWARE\${Vendor}\${ShortName}" 
  !define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

;--------------------------------
;Pages
 
  ; License page
  !insertmacro MUI_PAGE_LICENSE $(license)
 
  ; Installation directory selection
  !insertmacro MUI_PAGE_DIRECTORY
  
  ; Installation...
  !insertmacro MUI_PAGE_INSTFILES
  
  ; Finish Page
  !insertmacro MUI_PAGE_FINISH
  
  ; Uninstall confirmation
  !insertmacro MUI_UNPAGE_CONFIRM
  
  ;Uninstall
  !insertmacro MUI_UNPAGE_INSTFILES
 
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
  !insertmacro MUI_LANGUAGE "French"

  LicenseLangString license ${LANG_ENGLISH} "${DISTPATH}\LICENSE.txt"
  LicenseLangString license ${LANG_FRENCH} "${DISTPATH}\LICENSE.txt"
  
;--------------------------------
;Reserve Files
  
  ;If you are using solid compression, files that are required before
  ;the actual installation should be stored first in the data block,
  ;because this will make your installer start faster.
  
  !insertmacro MUI_RESERVEFILE_LANGDLL
 
;--------------------------------
;Language Strings

  ;DisplayName
  LangString DisplayName ${LANG_ENGLISH} "Minarca Backup"
  LangString DisplayName ${LANG_FRENCH} "Sauvegarde Minarca"

  LangString APP_IS_RUNNING ${LANG_ENGLISH} "$(DisplayName) is currently running. To continue with the installation, verify that no backup is currently in progress and close $(DisplayName) application."
  LangString APP_IS_RUNNING ${LANG_FRENCH} "$(DisplayName) est en cours d'exécution. Pour poursuivre l'installation, vérifiez qu'aucune sauvegarde n'est en cours et fermez l'application $(DisplayName)."
 
  ;Description
  LangString DESC_SecAppFiles ${LANG_ENGLISH} "Application files copy"
  LangString DESC_SecAppFiles ${LANG_FRENCH} "Copie des fichiers"

;--------------------------------
;Global Variables
Var ShortcutIconPath ; Variable to hold the actual icon path used for shortcuts/registry
Var HeaderName       ; Variable to store the value read from setup.cfg for link names

;--------------------------------
;Installer Sections

Section "Installation of $(DisplayName)" SecAppFiles
  
  ; Install for all
  SetShellVarContext all

  ; Check if minarca is running
  retry_label:
  DetailPrint "Check if application is running..."
  nsExec::ExecToLog `cmd /c "%SystemRoot%\System32\tasklist.exe /FI $\"IMAGENAME eq ${AppExeFile}$\" | %SystemRoot%\System32\find /I $\"${AppExeFile}$\" "`
  Pop $0  ; Get the exit code of the command
  ; Check if the exit code is zero using ${If}
  ${If} $0 == 0
      MessageBox MB_ABORTRETRYIGNORE|MB_ICONEXCLAMATION "$(APP_IS_RUNNING)" IDRETRY retry_label IDIGNORE ignore_label
      Abort
  ${EndIf}
  ignore_label:

  ; Remove previous files
  RMDir /r "$INSTDIR"

  ; Add files
  SetOutPath $INSTDIR
  SetOverwrite on
  File /r ".\"

  ; Add installer info to registry
  WriteRegStr HKLM "SOFTWARE\${Vendor}\${ShortName}" "" "$INSTDIR"

  ; Enable Long file path support by default.
  WriteRegDWORD HKLM "SYSTEM\CurrentControlSet\Control\FileSystem" "LongPathsEnabled" "1"

  ; --- Determine the icon path to be used for shortcuts and registry entries ---
  ; Initialize with the path to the default internal favicon
  StrCpy $ShortcutIconPath "$INSTDIR\${DEFAULT_FAVICON}"

  ; Copy custom config
  ${If} ${FileExists} "$EXEDIR\setup.cfg"
    CopyFiles "$EXEDIR\setup.cfg" "$INSTDIR\minarca.cfg"
  ${EndIf}
  
  ; If a sidecar favicon.ico exists, copy it to $INSTDIR\favicon.ico and update the icon path
  ${If} ${FileExists} "$EXEDIR\favicon.ico"
    CopyFiles "$EXEDIR\favicon.ico" "$INSTDIR\favicon.ico" ; Copy sidecar to root of install dir
    StrCpy $ShortcutIconPath "$INSTDIR\favicon.ico"        ; Use sidecar for shortcuts and registry
  ${EndIf}
  ; Other sidecar files
  ${If} ${FileExists} "$EXEDIR\favicon.png"
    CopyFiles "$EXEDIR\favicon.png" "$INSTDIR"
  ${EndIf}
  ${If} ${FileExists} "$EXEDIR\header_logo.png"
    CopyFiles "$EXEDIR\header_logo.png" "$INSTDIR"
  ${EndIf}
  ; --- End icon path determination ---

  ; Define Custom Protocol for Toast Notification
  DeleteRegKey HKCR "minarca"
  WriteRegStr HKCR "minarca" "" "URL:minarca"
  WriteRegStr HKCR "minarca" "URL Protocol" ""
  WriteRegStr HKCR "minarca\DefaultIcon" "" "$ShortcutIconPath" ; Use the determined icon path
  WriteRegStr HKCR "minarca\shell" "" ""
  WriteRegStr HKCR "minarca\shell\Open" "" ""
  WriteRegStr HKCR "minarca\shell\Open\command" "" "$INSTDIR\minarcaw.exe ui"

  !define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayName" "$(DisplayName)"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayIcon" "$ShortcutIconPath" ; Use the determined icon path
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayVersion" "${AppVersion}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "Publisher" "${Vendor}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoModify" "1"
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoRepair" "1"
 
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Create startup menu
  CreateDirectory "$SMPROGRAMS\$(DisplayName)"
  
  ; Use HeaderName for shortcuts if available, otherwise fall back to DisplayName
  ${If} $HeaderName != ""
    CreateShortCut "$DESKTOP\$HeaderName.lnk" "$INSTDIR\minarcaw.exe" "" "$ShortcutIconPath" 0
    CreateShortCut "$SMPROGRAMS\$HeaderName.lnk" "$INSTDIR\minarcaw.exe" "" "$ShortcutIconPath" 0
  ${Else}
    CreateShortCut "$DESKTOP\$(DisplayName).lnk" "$INSTDIR\minarcaw.exe" "" "$ShortcutIconPath" 0
    CreateShortCut "$SMPROGRAMS\$(DisplayName).lnk" "$INSTDIR\minarcaw.exe" "" "$ShortcutIconPath" 0
  ${EndIf}

SectionEnd

;--------------------------------
;Installer Functions


!define ICON_SMALL     0
!define ICON_BIG       1

Var hIconBig
Var hIconSmall

Function .onInit

  ; When running 64bits, read and write to 64bits registry.
  SetRegView 64

  ; Set installation directory according to bitness
  ${If} $InstDir == ""
    StrCpy $InstDir "$LOCALAPPDATA\${SHORTNAME}"
  ${EndIf}

  ; --- Determine the display name ---
  ; Read header_name from setup.cfg
  ${ConfigRead} "$EXEDIR\${CFG_FILENAME}" "header_name=" $HeaderName

  ${If} $HeaderName != ""
    Name "${HeaderName} power by Minarca"
  ${Else}
    Name "${AppName}"
  ${EndIf}

  !insertmacro MUI_LANGDLL_DISPLAY

FunctionEnd


; Clean up icon handles
Function .onGUIEnd
  ${If} $hIconBig <> 0
    System::Call 'user32::DestroyIcon(p $hIconBig)'
  ${EndIf}
  ${If} $hIconSmall <> 0
    System::Call 'user32::DestroyIcon(p $hIconSmall)'
  ${EndIf}
FunctionEnd

;--------------------------------
;Uninstaller Section
 
Section "Uninstall"

  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}"
  DeleteRegKey HKLM  "SOFTWARE\${Vendor}\${AppName}"
  
  ; remove shortcuts, if any.
  Delete "$DESKTOP\$(DisplayName).lnk"
  Delete "$SMPROGRAMS\$(DisplayName).lnk"
  
  ; remove files
  RMDir /r "$INSTDIR"
 
SectionEnd

;--------------------------------
;Uninstaller Functions

Function un.onInit

  ; When running 64bits, read and write to 64bits registry.
  SetRegView 64
  
  ; Uninstall for all user
  SetShellVarContext all

  !insertmacro MUI_UNGETLANGUAGE
  
FunctionEnd