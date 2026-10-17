; Inno Setup script - ABIX NINJA PRO ULTRA v3
[Setup]
AppName=ABIX NINJA PRO ULTRA
AppVersion=3.0
AppPublisher=Abu Bakkar
DefaultDirName={autopf}\AbixNinja
DefaultGroupName=ABIX NINJA
OutputDir=installer_output
OutputBaseFilename=AbixNinja_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\AbixNinja.exe
DisableProgramGroupPage=yes
UninstallDisplayName=ABIX NINJA PRO ULTRA

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "dist\AbixNinja\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\ABIX NINJA"; Filename: "{app}\AbixNinja.exe"
Name: "{autodesktop}\ABIX NINJA"; Filename: "{app}\AbixNinja.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AbixNinja.exe"; Description: "Play ABIX NINJA now"; Flags: nowait postinstall skipifsilent
