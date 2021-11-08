; Minarca client
;
; Copyright (C) 2021 IKUS Software inc. All rights reserved.
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
 
;--------------------------------
;Includes

  Unicode True
  SetCompressor bzip2

!include "MUI2.nsh"
!include "Sections.nsh"
!include "x64.nsh"
 
;--------------------------------
;Configuration
 
  ;General
  Name "${AppName}"
  VIProductVersion "${AppVersion}"
  VIAddVersionKey "ProductName" "${AppName}"
  VIAddVersionKey "Comments" "Automatically saves your data online for easy access at any time while travelling or in case of equipment loss or breakage."
  VIAddVersionKey "CompanyName" "${Vendor}"
  VIAddVersionKey "LegalCopyright" "© ${Vendor}"
  VIAddVersionKey "FileDescription" "${AppName} ${AppVersion} Installer"
  VIAddVersionKey "FileVersion" "${AppVersion}"
  OutFile "${OutFile}"
  
  ; Define icon
  !define MUI_ICON "minarca_client/ui/theme/minarca.ico"
  !define MUI_UNICON "minarca_client/ui/theme/minarca.ico"
 
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
  !define MUI_FINISHPAGE_RUN
  !define MUI_FINISHPAGE_RUN_TEXT $(RunMinarca)
  !define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
  !insertmacro MUI_PAGE_FINISH
  
  ; Uninstall confirmation
  !insertmacro MUI_UNPAGE_CONFIRM
  
  ;Uninstall
  !insertmacro MUI_UNPAGE_INSTFILES
 
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
  !insertmacro MUI_LANGUAGE "French"

  LicenseLangString license ${LANG_ENGLISH} "LICENSE.txt"
  LicenseLangString license ${LANG_FRENCH} "LICENSE.txt"
  
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

  LangString APP_IS_RUNNING ${LANG_ENGLISH} "The installation process detected ${AppName} is running. Please close it and try again."
  LangString APP_IS_RUNNING ${LANG_FRENCH} "Le processus d'installation a détecté que ${AppName} est en cours d'exécution. S'il vous plaît, fermez l'application et essayez à nouveau."
 
  ;Description
  LangString DESC_SecAppFiles ${LANG_ENGLISH} "Application files copy"
  LangString DESC_SecAppFiles ${LANG_FRENCH} "Copie des fichiers"
  
  LangString RunMinarca ${LANG_ENGLISH} "Start ${AppName}"
  LangString RunMinarca ${LANG_FRENCH} "Démarrer ${AppName}"
 
;--------------------------------
;Installer Sections
 
Section "Installation of $(DisplayName)" SecAppFiles
  
  ; Remove previous files
  RMDir /r "$INSTDIR"
  
  ; Add files
  SetOutPath $INSTDIR
  SetOverwrite on
  File /r ".\"
  
  ;Store install folder
  WriteRegStr HKLM "SOFTWARE\${Vendor}\${ShortName}" "" $INSTDIR
 
  !define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayName" "$(DisplayName)"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayIcon" "$INSTDIR\minarca_client\ui\theme\minarca.ico"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayVersion" "${AppVersion}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "Publisher" "${Vendor}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoModify" "1"
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoRepair" "1"
 
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Create startup menu
  CreateDirectory "$SMPROGRAMS\$(DisplayName)"
  CreateShortCut "$DESKTOP\$(DisplayName).lnk" "$INSTDIR\minarcaw.exe" "" "$INSTDIR\minarca_client\ui\theme\minarca.ico" 0
  CreateShortCut "$SMPROGRAMS\$(DisplayName)\${AppName}.lnk" "$INSTDIR\minarcaw.exe" "" "$INSTDIR\minarca_client\ui\theme\minarca.ico" 0

SectionEnd
 
 
;--------------------------------
;Installer Functions
 
Function .onInit

  ; When running 64bits, read and write to 64bits registry.
  SetRegView 64
  
  ; Install for current user
  SetShellVarContext current

  ; Set installation directory according to bitness
  ${If} $InstDir == ""
    StrCpy $InstDir "$LOCALAPPDATA\${SHORTNAME}"
  ${EndIf}
  
  !insertmacro MUI_LANGDLL_DISPLAY
  
FunctionEnd

;--------------------------------
;Finish Section

Function LaunchLink
    ExecShell "" "$SMPROGRAMS\$(DisplayName)\${AppName}.lnk"
FunctionEnd

;--------------------------------
;Uninstaller Section
 
Section "Uninstall"

  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}"
  DeleteRegKey HKLM  "SOFTWARE\${Vendor}\${AppName}"
  ; remove shortcuts, if any.
  Delete "$SMPROGRAMS\${AppName}\*.*"
  RMDir /r "$SMPROGRAMS\${AppName}"
  Delete "$DESKTOP\$(DisplayName).lnk"
  ; remove files
  RMDir /r "$INSTDIR"
 
SectionEnd

;--------------------------------
;Uninstaller Functions

Function un.onInit

  ; When running 64bits, read and write to 64bits registry.
  SetRegView 64
  
  ; Uninstall for all user
  SetShellVarContext current

  !insertmacro MUI_UNGETLANGUAGE
  
FunctionEnd
