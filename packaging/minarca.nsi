; Minarca client
;
; Copyright (C) 2025 IKUS Software. All rights reserved.
; IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
; Use is subject to license terms.
;
; This script is used by NSIS to build a Windows installer for Minarca Client.
;

; Displayed to the user
!define APP_NAME "Minarca"

; Used for paths and registry.
!define APP_CODE_NAME "minarca"
!define APP_VENDOR "Ikus Soft inc."
!define AppExeFile "minarcaw.exe"

; The following should be overide by pyinstaller script.
;!define APP_VERSION "1.1.1.1"
;!define OutFile "minarca-installer-dev.exe"

; Constant values
!define SETUP_CFG "setup.cfg"
!define MINARCA_CFG "minarca.cfg"

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
  Name "${InstallerDisplayName}"
  VIProductVersion "${APP_VERSION}"
  VIAddVersionKey "ProductName" "${APP_NAME}"
  VIAddVersionKey "Comments" "Automatically saves your data online for easy access at any time while travelling or in case of equipment loss or breakage."
  VIAddVersionKey "CompanyName" "${APP_VENDOR}"
  VIAddVersionKey "LegalCopyright" "© ${APP_VENDOR}"
  VIAddVersionKey "FileDescription" "${APP_NAME} ${APP_VERSION} Installer"
  VIAddVersionKey "FileVersion" "${APP_VERSION}"
  OutFile "${OutFile}"
  
  ; Define icon
  !define DEFAULT_FAVICON "_internal\minarca_client\ui\theme\resources\favicon.ico"
  !define MUI_ICON "${SPECPATH}\setup.ico"
  !define MUI_UNICON "${SPECPATH}\setup.ico"
 
  ;Folder selection page
  InstallDir "$PROGRAMFILES64\Minarca"
 
  ;Get install folder from registry if available
  InstallDirRegKey HKLM "SOFTWARE\${APP_VENDOR}\${APP_CODE_NAME}" ""
 
  ;Request application privileges
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
  !define MUI_LANGDLL_REGISTRY_KEY "SOFTWARE\${APP_VENDOR}\${APP_CODE_NAME}" 
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

  LangString PowerBy ${LANG_ENGLISH} "power by Minarca"
  LangString PowerBy ${LANG_FRENCH} "propulsé par Minarca"

  LangString APP_IS_RUNNING ${LANG_ENGLISH} "${HeaderName} is currently running. To continue with the installation, verify that no backup is currently in progress and close ${HeaderName} application."
  LangString APP_IS_RUNNING ${LANG_FRENCH} "${HeaderName} est en cours d'exécution. Pour poursuivre l'installation, vérifiez qu'aucune sauvegarde n'est en cours et fermez l'application ${HeaderName}."
 
  ;Description
  LangString DESC_SecAppFiles ${LANG_ENGLISH} "Application files copy"
  LangString DESC_SecAppFiles ${LANG_FRENCH} "Copie des fichiers"

;--------------------------------
;Global Variables
Var ShortcutIconPath ; Variable to hold the actual icon path used for shortcuts/registry
Var HeaderName       ; Variable to store the value read from setup.cfg for link names
Var InstallerDisplayName  ; Variable to store the installer name.

;--------------------------------
;Installer Sections

Section "Installation of ${InstallerDisplayName}" SecAppFiles
  
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
  WriteRegStr HKLM "SOFTWARE\${APP_VENDOR}\${APP_CODE_NAME}" "" "$INSTDIR"

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

  !define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_CODE_NAME}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayName" "${InstallerDisplayName}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayIcon" "$ShortcutIconPath"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "Publisher" "${APP_VENDOR}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoModify" "1"
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoRepair" "1"
 
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Create Shortcuts
  CreateShortCut "$DESKTOP\$HeaderName.lnk" "$INSTDIR\minarcaw.exe" "" "$ShortcutIconPath" 0
  CreateShortCut "$SMPROGRAMS\$HeaderName.lnk" "$INSTDIR\minarcaw.exe" "" "$ShortcutIconPath" 0

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
    StrCpy $InstDir "$LOCALAPPDATA\${APP_CODE_NAME}"
  ${EndIf}

  ; Read header_name from setup.cfg
  ${ConfigRead} "$EXEDIR\${SETUP_CFG}" "header_name=" $HeaderName

  ${If} $HeaderName != ""
    StrCpy $InstallerDisplayName "${HeaderName} $(PowerBy)"
  ${Else}
    StrCpy $InstallerDisplayName "$(DisplayName)"
    StrCpy $HeaderName "$APP_NAME"
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

  ; Read header_name from minarca.cfg
  ${ConfigRead} "$EXEDIR\${MINARCA_CFG}" "header_name=" $HeaderName

  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_CODE_NAME}"
  DeleteRegKey HKLM  "SOFTWARE\${APP_VENDOR}\${APP_CODE_NAME}"
  
  ; remove default and custom shortcuts
  Delete "$DESKTOP\$(DisplayName).lnk"
  Delete "$DESKTOP\${HeaderName}.lnk"
  Delete "$SMPROGRAMS\$(DisplayName).lnk"
  Delete "$SMPROGRAMS\${HeaderName}.lnk"
  
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