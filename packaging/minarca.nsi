; Minarca Client – Windows Installer (Reorganized)
;
; Copyright (C) 2025 IKUS Software.
; PROPRIETARY/CONFIDENTIAL – Use subject to license terms.

;--------------------------------
; Build/Meta Defines

!define APP_NAME         "Minarca"
!define APP_CODE_NAME    "minarca"
!define APP_EXE_FILE     "minarcaw.exe"
!define APP_VENDOR       "Ikus Soft inc."

; These are expected to be overridden externally (e.g., by pyinstaller)
;!define APP_VERSION     "1.1.1.1"
;!define APP_DESCRIPTION "App description"
;!define FIXED_VERSION   "1.1.1.1"
;!define OUT_FILE        "minarca-installer-dev.exe"

; Filenames in package / sidecar
!define DEFAULT_FAVICON  "_internal\minarca_client\ui\theme\resources\favicon.ico"
!define MINARCA_CFG      "minarca.cfg"
!define SETUP_CFG        "setup.cfg"

; Paths/Registry
!define REG_APP_KEY         "SOFTWARE\${APP_VENDOR}\${APP_CODE_NAME}"
!define REG_APP_ROOT        "HKLM"
!define REG_UNINSTALL_KEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_CODE_NAME}"
!define REG_UNINSTALL_ROOT  "HKLM"
!define PROTOCOL_NAME       "minarca"
!define PROTOCOL_ROOT       "HKCR"

;--------------------------------
; Includes / Settings

!include "MUI2.nsh"
!include "Sections.nsh"
!include "x64.nsh"
!include "WinMessages.nsh"
!include "LogicLib.nsh"
!include "StrFunc.nsh"
!include "TextFunc.nsh"
!insertmacro ConfigRead

; Use unicode
Unicode True

; Force lzma for compression
SetCompressor lzma

; Request admin (needed for HKLM writes and ProgramFiles)
RequestExecutionLevel admin

; Default install dir and registry back-reference
InstallDir "$PROGRAMFILES64\Minarca"
InstallDirRegKey ${REG_APP_ROOT} "${REG_APP_KEY}" ""

;--------------------------------
; Global Vars
Var ShortcutIconPath         ; path to icon used for shortcuts/registry
Var HeaderName               ; value from setup/minarca.cfg for link names
Var InstallerDisplayName     ; visible product name ("HeaderName power by Minarca" or fallback)

;--------------------------------
; Version Info / Binary Output
Name $InstallerDisplayName
VIProductVersion "${FIXED_VERSION}"
VIAddVersionKey "ProductName"     "${APP_NAME}"
VIAddVersionKey "Comments"        "${APP_DESCRIPTION}"
VIAddVersionKey "CompanyName"     "${APP_VENDOR}"
VIAddVersionKey "LegalCopyright"  "© ${APP_VENDOR}"
VIAddVersionKey "FileDescription" "${APP_NAME} ${APP_VERSION} Installer"
VIAddVersionKey "ProductVersion"  "${APP_VERSION}"
VIAddVersionKey "FileVersion"     "${APP_VERSION}"
OutFile "${OUT_FILE}"

;--------------------------------
; UI / Icons
!define MUI_ICON   "${SPECPATH}\setup.ico"
!define MUI_UNICON "${SPECPATH}\setup.ico"

!define MUI_ABORTWARNING
!define MUI_LANGDLL_ALLLANGUAGES
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY  "SOFTWARE\${APP_VENDOR}\${APP_CODE_NAME}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

;--------------------------------
; Wizard Pages
!insertmacro MUI_PAGE_LICENSE $(license)
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Languages
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"

LicenseLangString license ${LANG_ENGLISH} "${DISTPATH}\LICENSE.txt"
LicenseLangString license ${LANG_FRENCH}  "${DISTPATH}\LICENSE.txt"

;--------------------------------
; Reserved Files (for solid compression speed)
!insertmacro MUI_RESERVEFILE_LANGDLL

;--------------------------------
; Localized Strings
LangString DisplayName ${LANG_ENGLISH} "Minarca Backup"
LangString DisplayName ${LANG_FRENCH}  "Sauvegarde Minarca"

LangString PowerBy ${LANG_ENGLISH} "power by Minarca"
LangString PowerBy ${LANG_FRENCH}  "propulsé par Minarca"

LangString AppIsRunning ${LANG_ENGLISH} "$HeaderName is currently running. To continue with the installation, verify that no backup is currently in progress and close $HeaderName application."
LangString AppIsRunning ${LANG_FRENCH}  "$HeaderName est en cours d'exécution. Pour poursuivre l'installation, vérifiez qu'aucune sauvegarde n'est en cours et fermez l'application $HeaderName."

;--------------------------------
; Helper Functions

; Ensure app not running; offer Retry/Ignore/Abort
Function EnsureAppNotRunning
  retry_check:
    DetailPrint "Checking if ${APP_EXE_FILE} is running..."
    nsExec::ExecToLog `cmd /c "%SystemRoot%\System32\tasklist.exe /FI $\"IMAGENAME eq ${APP_EXE_FILE}$\" | %SystemRoot%\System32\find /I $\"${APP_EXE_FILE}$\" "`
    Pop $0
    ${If} $0 == 0
      MessageBox MB_ABORTRETRYIGNORE|MB_ICONEXCLAMATION "$(AppIsRunning)" IDRETRY retry_check IDIGNORE continue_install
      Abort
    ${EndIf}
  continue_install:
FunctionEnd

; Register custom URL protocol (for toast notifications)
Function RegisterProtocol
  DeleteRegKey ${PROTOCOL_ROOT} "${PROTOCOL_NAME}"
  WriteRegStr ${PROTOCOL_ROOT} "${PROTOCOL_NAME}" "" "URL:${PROTOCOL_NAME}"
  WriteRegStr ${PROTOCOL_ROOT} "${PROTOCOL_NAME}" "URL Protocol" ""
  WriteRegStr ${PROTOCOL_ROOT} "${PROTOCOL_NAME}\DefaultIcon" "" "$ShortcutIconPath"
  WriteRegStr ${PROTOCOL_ROOT} "${PROTOCOL_NAME}\shell" "" ""
  WriteRegStr ${PROTOCOL_ROOT} "${PROTOCOL_NAME}\shell\Open" "" ""
  WriteRegStr ${PROTOCOL_ROOT} "${PROTOCOL_NAME}\shell\Open\command" "" "$INSTDIR\${APP_EXE_FILE} ui"
FunctionEnd

; Register uninstaller metadata
Function RegisterUninstall
  WriteRegStr   ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}" "DisplayName"   "$InstallerDisplayName"
  WriteRegStr   ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}" "DisplayIcon"    "$ShortcutIconPath"
  WriteRegStr   ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr   ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}" "Publisher"      "${APP_VENDOR}"
  WriteRegStr   ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}" "NoRepair" 1
FunctionEnd

; Create common shortcuts
Function CreateAppShortcuts
  CreateShortCut "$DESKTOP\$HeaderName.lnk"    "$INSTDIR\${APP_EXE_FILE}" "" "$ShortcutIconPath" 0
  CreateShortCut "$SMPROGRAMS\$HeaderName.lnk" "$INSTDIR\${APP_EXE_FILE}" "" "$ShortcutIconPath" 0
FunctionEnd

;--------------------------------
; .onInit
Function .onInit

  SetRegView 64          ; 64-bit registry view
  SetShellVarContext all ; Install for all users

  ; First attempt: read header_name from sidecar setup.cfg (next to installer)
  ${ConfigRead} "$INSTDIR\${MINARCA_CFG}" "header_name=" $HeaderName
  
  ${If} $HeaderName != ""
    StrCpy $InstallerDisplayName "$HeaderName $(PowerBy)"
  ${Else}
    StrCpy $InstallerDisplayName "$(DisplayName)"
    StrCpy $HeaderName "${APP_NAME}"
  ${EndIf}
  
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

;--------------------------------
; Sections

Section "Install ${APP_NAME}" SecAppFiles
  SectionIn RO

  ; Ensure app not running
  Call EnsureAppNotRunning

  ; Clean previous install directory
  RMDir /r "$INSTDIR"

  ; Copy payload
  SetOutPath $INSTDIR
  SetOverwrite on
  File /r ".\"

  ; Persist install path
  WriteRegStr ${REG_APP_ROOT} "${REG_APP_KEY}" "" "$INSTDIR"

  ; Enable long paths
  WriteRegDWORD HKLM "SYSTEM\CurrentControlSet\Control\FileSystem" "LongPathsEnabled" 1

  ; Resolve icon to use for shortcuts/registry (sidecar favicon.ico > internal default)
  ; Start with internal favicon inside package
  StrCpy $ShortcutIconPath "$INSTDIR\${DEFAULT_FAVICON}"

  ; If caller placed a sidecar favicon.ico next to installer, prefer it
  ${If} ${FileExists} "$EXEDIR\favicon.ico"
    CopyFiles "$EXEDIR\favicon.ico" "$INSTDIR\favicon.ico"
    StrCpy $ShortcutIconPath "$INSTDIR\favicon.ico"
  ${EndIf}

  ; Optional sidecar assets
  ${If} ${FileExists} "$EXEDIR\${SETUP_CFG}"
    CopyFiles "$EXEDIR\${SETUP_CFG}" "$INSTDIR\${MINARCA_CFG}"
  ${EndIf}
  ${If} ${FileExists} "$EXEDIR\favicon.png"
    CopyFiles "$EXEDIR\favicon.png" "$INSTDIR"
  ${EndIf}
  ${If} ${FileExists} "$EXEDIR\header_logo.png"
    CopyFiles "$EXEDIR\header_logo.png" "$INSTDIR"
  ${EndIf}

  ; Define Custom Protocol for Toast Notification
  Call RegisterProtocol

  ; Register uninstaller metadata
  Call RegisterUninstall

  ; Generate uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Create shortcuts
  Call CreateAppShortcuts
SectionEnd

;--------------------------------
; Uninstall Section

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey ${REG_UNINSTALL_ROOT} "${REG_UNINSTALL_KEY}"
  DeleteRegKey ${REG_APP_ROOT}       "${REG_APP_KEY}"
  DeleteRegKey ${PROTOCOL_ROOT}      "${PROTOCOL_NAME}"

  ; Remove shortcuts (both default/fallback and header-based, for safety)
  Delete "$DESKTOP\$(DisplayName).lnk"
  Delete "$DESKTOP\$HeaderName.lnk"
  Delete "$SMPROGRAMS\$(DisplayName).lnk"
  Delete "$SMPROGRAMS\$HeaderName.lnk"

  ; Remove files
  RMDir /r "$INSTDIR"
SectionEnd

;--------------------------------
; Uninstaller init (keep minimal; most is in section)
Function un.onInit
  
  SetRegView 64          ; 64-bit registry view
  SetShellVarContext all ; Install for all users

  !insertmacro MUI_UNGETLANGUAGE

  ; Read header_name from minarca.cfg
  ${ConfigRead} "$INSTDIR\${MINARCA_CFG}" "header_name=" $HeaderName
  
  ${If} $HeaderName != ""
    StrCpy $InstallerDisplayName "$HeaderName $(PowerBy)"
  ${Else}
    StrCpy $InstallerDisplayName "$(DisplayName)"
    StrCpy $HeaderName "${APP_NAME}"
  ${EndIf}

FunctionEnd
