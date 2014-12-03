; Displayed to the user
!define AppName "Minarca"
; Used for paths
!define ShortName "minarca"
!define Vendor "Patrik Dufresne Service Logiciel"
!define LicenseFile "LICENSE.txt"
!define AppExeFile ""
 
;--------------------------------
;Includes

  !include "MUI2.nsh"
  !include "Sections.nsh"
  !include "x64.nsh"

SetCompressor bzip2
 
;--------------------------------
;Configuration
 
  ;General
  Name "${AppName}"
  VIProductVersion "${AppVersion}"
  VIAddVersionKey "ProductName" "${AppName}"
  VIAddVersionKey "Comments" "A test comment"
  VIAddVersionKey "CompanyName" "${Vendor}"
  VIAddVersionKey "LegalCopyright" "© ${Vendor}"
  VIAddVersionKey "FileDescription" "${AppName} ${AppVersion} Installer"
  VIAddVersionKey "FileVersion" "${AppVersion}"
  OutFile "setup.exe"
  
  ; Define icon
  !define MUI_ICON "minarca.ico"
  !define MUI_UNICON "minarca.ico"
 
  ;Folder selection page
  InstallDir ""
 
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
  !insertmacro MUI_PAGE_LICENSE "${LicenseFile}"
 
  ; Installation directory selection
  !insertmacro MUI_PAGE_DIRECTORY
  
  ; Installation...
  !insertmacro MUI_PAGE_INSTFILES
  
  ; Finish Page
  !define MUI_FINISHPAGE_RUN
  !define MUI_FINISHPAGE_RUN_TEXT "Start ${AppName}"
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
 
;--------------------------------
;Reserve Files
  
  ;If you are using solid compression, files that are required before
  ;the actual installation should be stored first in the data block,
  ;because this will make your installer start faster.
  
  !insertmacro MUI_RESERVEFILE_LANGDLL
 
;--------------------------------
;Language Strings
 
  ;Description
  LangString DESC_SecAppFiles ${LANG_ENGLISH} "Application files copy"
  LangString DESC_SecAppFiles ${LANG_FRENCH} "Copie des fichiers"
 
;--------------------------------
;Installer Sections
 
Section "Installation of ${AppName}" SecAppFiles
  
  ; Add files
  SetOutPath $INSTDIR
  SetOverwrite on
  File /r ".\"
  
  ;Store install folder
  WriteRegStr HKLM "SOFTWARE\${Vendor}\${ShortName}" "" $INSTDIR
 
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}" "DisplayName" "${AppName}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}" "NoModify" "1"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}" "NoRepair" "1"
 
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
 
SectionEnd
 
 
Section "Start menu shortcuts" SecCreateShortcut

  SectionIn 1	; Can be unselected
  CreateDirectory "$SMPROGRAMS\${AppName}"
  ${If} ${RunningX64}
    CreateShortCut "$SMPROGRAMS\${AppName}\${AppName}.lnk" "$INSTDIR\bin\minarca64.exe" "" "$INSTDIR\bin\minarca64.exe" 0
  ${Else}
    CreateShortCut "$SMPROGRAMS\${AppName}\${AppName}.lnk" "$INSTDIR\bin\minarca.exe" "" "$INSTDIR\bin\minarca.exe" 0
  ${EndIf}
  
SectionEnd
 
;--------------------------------
;Descriptions
 
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecAppFiles} $(DESC_SecAppFiles)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
 
;--------------------------------
;Installer Functions
 
Function .onInit

  ; Set installation directory accoding to bitness
  ${If} $InstDir == ""
  	StrCpy $InstDir "$PROGRAMFILES\${SHORTNAME}"
    ${If} ${RunningX64}
        StrCpy $InstDir "$PROGRAMFILES64\${SHORTNAME}"
    ${EndIf}
  ${EndIf}
  
  !insertmacro MUI_LANGDLL_DISPLAY
  
FunctionEnd

;--------------------------------
;Finish Section

Function LaunchLink
	ExecShell "" "$SMPROGRAMS\${AppName}\${AppName}.lnk"
FunctionEnd

;--------------------------------
;Uninstaller Section
 
Section "Uninstall"
 
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}"
  DeleteRegKey HKLM  "SOFTWARE\${Vendor}\${AppName}"
  ; remove shortcuts, if any.
  Delete "$SMPROGRAMS\${AppName}\*.*"
  ; remove files
  RMDir /r "$INSTDIR"
 
SectionEnd

;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MUI_UNGETLANGUAGE
  
FunctionEnd
