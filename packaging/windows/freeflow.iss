; Inno Setup script for the Windows installer.
;   iscc /DAppVersion=0.2.0 packaging\windows\freeflow.iss
; Expects the PyInstaller output in dist\FreeFlow.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F1C2E7A-4B8D-4E35-9A61-F3E0C2B9D4A7}
AppName=FreeFlow
AppVersion={#AppVersion}
AppPublisher=FreeFlow
AppVerName=FreeFlow {#AppVersion}
; Per-user install: no admin prompt, and settings stay with the user.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\FreeFlow
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\FreeFlow.exe
SetupIconFile=..\build\icon.ico
OutputDir=..\..\dist
OutputBaseFilename=FreeFlow-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "startup"; Description: "Start FreeFlow when I sign in"; GroupDescription: "Options:"
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Options:"; Flags: unchecked

[Files]
Source: "..\..\dist\FreeFlow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\FreeFlow"; Filename: "{app}\FreeFlow.exe"
Name: "{userdesktop}\FreeFlow"; Filename: "{app}\FreeFlow.exe"; Tasks: desktopicon

[Registry]
; Same value the app's "Open FreeFlow when I log in" setting manages.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "FreeFlow"; ValueData: """{app}\FreeFlow.exe"""; Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\FreeFlow.exe"; Description: "Open FreeFlow now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM FreeFlow.exe"; Flags: runhidden; RunOnceId: "StopFreeFlow"
