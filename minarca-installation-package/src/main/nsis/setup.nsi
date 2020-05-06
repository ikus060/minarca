; Displayed to the user
!define AppName "Minarca"
; Used for paths
!define ShortName "minarca"
!define Vendor "Ikus Soft inc."
!define AppExeFile ""
 
;--------------------------------
;Includes

  !include "MUI2.nsh"
  !include "Sections.nsh"
  !include "x64.nsh"

SetCompressor bzip2

  ; Include Java Install
  !addincludedir ${includedir}
  !addplugindir ${plugindir}
  !define JRE_VERSION "1.8"
  # JAVA 8u241
  !define JRE_URL "https://javadl.oracle.com/webapps/download/AutoDL?BundleId=241534_1f5b5a70bf22433b84d0e960903adac8"
  !define JRE_URL_64 "https://javadl.oracle.com/webapps/download/AutoDL?BundleId=241536_1f5b5a70bf22433b84d0e960903adac8"
  !include "JREDyna_Inetc.nsh"
  !include "nsProcess.nsh"
  

;--------------------------------
;Configuration
 
  ;General
  Name "${AppName}"
  VIProductVersion "${AppVersion}"
  VIAddVersionKey "ProductName" "${AppName}"
  VIAddVersionKey "Comments" "Automatically saves your data online for easy access at any time while travelling or in case of equipment loss or breakage."
  VIAddVersionKey "CompanyName" "${Vendor}"
  VIAddVersionKey "LegalCopyright" "� ${Vendor}"
  VIAddVersionKey "FileDescription" "${AppName} ${AppVersion} Installer"
  VIAddVersionKey "FileVersion" "${AppVersion}"
  OutFile "${OutFile}"
  
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
  !insertmacro MUI_PAGE_LICENSE $(license)
 
  ; Java download page 
  !insertmacro CUSTOM_PAGE_JREINFO
 
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
  
  !insertmacro JREINFO_LANGUAGE
  
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
  LangString APP_IS_RUNNING ${LANG_FRENCH} "Le processus d'installation a d�tect� que ${AppName} est en cours d'ex�cution. S'il vous pla�t, fermez l'application et essayez � nouveau."
 
  ;Description
  LangString DESC_SecAppFiles ${LANG_ENGLISH} "Application files copy"
  LangString DESC_SecAppFiles ${LANG_FRENCH} "Copie des fichiers"
  
  LangString RunMinarca ${LANG_ENGLISH} "Start ${AppName}"
  LangString RunMinarca ${LANG_FRENCH} "D�marrer ${AppName}"
 
;--------------------------------
;Installer Sections
 
Section "Installation of $(DisplayName)" SecAppFiles
  
  ; Remove files
  RMDir /r "$INSTDIR\lib"
  
  ; Add files
  SetOutPath $INSTDIR
  SetOverwrite on
  File /r ".\"
  
  ;Store install folder
  WriteRegStr HKLM "SOFTWARE\${Vendor}\${ShortName}" "" $INSTDIR
 
  !define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayName" "$(DisplayName)"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayIcon" "$INSTDIR\minarca.ico"
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayVersion" "${AppVersion}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "Publisher" "${Vendor}"
  WriteRegStr HKLM "${REG_UNINSTALL}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoModify" "1"
  WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoRepair" "1"
 
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Download and install java and tweak the secure protocol for download.
  ; http://forums.winamp.com/showthread.php?t=198596&page=14
  !define IE_NETCONFIG "Software\Microsoft\Windows\CurrentVersion\Internet Settings"
  ReadRegDWORD $9 HKCU "${IE_NETCONFIG}" "SecureProtocols"
  WriteRegDWORD HKCU "${IE_NETCONFIG}" "SecureProtocols" 0x00000A80
  call DownloadAndInstallJREIfNecessary
  WriteRegDWORD HKCU "${IE_NETCONFIG}" "SecureProtocols" $9

SectionEnd
 
 
Section "Start menu shortcuts" SecCreateShortcut

  SectionIn 1	; Can be unselected
  CreateDirectory "$SMPROGRAMS\$(DisplayName)"
  ${If} ${RunningX64}
    CreateShortCut "$DESKTOP\$(DisplayName).lnk" "$INSTDIR\bin\minarcaui64.exe" "" "$INSTDIR\minarca.ico" 0
    CreateShortCut "$SMPROGRAMS\${AppName}\$(DisplayName).lnk" "$INSTDIR\bin\minarcaui64.exe" "" "$INSTDIR\minarca.ico" 0
  ${Else}
    CreateShortCut "$DESKTOP\$(DisplayName).lnk" "$INSTDIR\bin\minarcaui.exe" "" "$INSTDIR\minarca.ico" 0
    CreateShortCut "$SMPROGRAMS\${AppName}\$(DisplayName).lnk" "$INSTDIR\bin\minarcaui.exe" "" "$INSTDIR\minarca.ico" 0
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

  ; When running 64bits, read and write to 64bits registry.
  SetRegView 64
  
  ; Install for current user
  SetShellVarContext current

  ; Set installation directory according to bitness
  ${If} $InstDir == ""
  	StrCpy $InstDir "$LOCALAPPDATA\${SHORTNAME}"
  ${EndIf}
  
  !insertmacro MUI_LANGDLL_DISPLAY
  
  ; Check if application is running.
  ${nsProcess::FindProcess} "minarca.exe" $R0
  StrCmp $R0 0 0 notRunning32
    MessageBox MB_OK|MB_ICONEXCLAMATION $(APP_IS_RUNNING) /SD IDOK
    Abort
  notRunning32:
  ${nsProcess::FindProcess} "minarca64.exe" $R0
  StrCmp $R0 0 0 notRunning64
    MessageBox MB_OK|MB_ICONEXCLAMATION $(APP_IS_RUNNING) /SD IDOK
    Abort
  notRunning64:
  ${nsProcess::FindProcess} "minarcaui.exe" $R0
  StrCmp $R0 0 0 notRunningUi32
    MessageBox MB_OK|MB_ICONEXCLAMATION $(APP_IS_RUNNING) /SD IDOK
    Abort
  notRunningUi32:
  ${nsProcess::FindProcess} "minarcaui64.exe" $R0
  StrCmp $R0 0 0 notRunningUi64
    MessageBox MB_OK|MB_ICONEXCLAMATION $(APP_IS_RUNNING) /SD IDOK
    Abort
  notRunningUi64:
    
FunctionEnd

;--------------------------------
;Finish Section

Function LaunchLink
	ExecShell "" "$SMPROGRAMS\${AppName}\$(DisplayName).lnk"
FunctionEnd

;--------------------------------
;Uninstaller Section
 
Section "Uninstall"

  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ShortName}"
  DeleteRegKey HKLM  "SOFTWARE\${Vendor}\${AppName}"
  ; remove shortcuts, if any.
  Delete "$SMPROGRAMS\$(AppName)\*.*"
  RMDir /r "$SMPROGRAMS\$(AppName)"
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
