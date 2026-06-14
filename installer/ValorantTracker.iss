#define MyAppName "Valorant Tracker"
#define MyAppExeName "ValorantTracker.exe"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Valorant Tracker"
#define MyAppURL "https://github.com/"
#define MyAppId "{{8E9991DB-A256-45CE-B6BC-A2AFBDF42D58}"
#define WebView2Bootstrapper "dependencies\MicrosoftEdgeWebView2Setup.exe"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\ValorantTracker
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
OutputBaseFilename=ValorantTrackerSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\ValorantTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifexist WebView2Bootstrapper
Source: "{#WebView2Bootstrapper}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: NeedsWebView2
#endif

[Dirs]
Name: "{userappdata}\ValorantTracker"; Flags: uninsneveruninstall
Name: "{userappdata}\ValorantTracker\logs"; Flags: uninsneveruninstall
Name: "{userappdata}\ValorantTracker\cache"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Logs"; Filename: "{userappdata}\ValorantTracker\logs"
Name: "{group}\Data Folder"; Filename: "{userappdata}\ValorantTracker"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "ValorantTracker"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "ValorantTrackerValorantWatcher"; Flags: uninsdeletevalue

[Run]
#ifexist WebView2Bootstrapper
Filename: "{tmp}\MicrosoftEdgeWebView2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Installing Microsoft Edge WebView2 Runtime..."; Flags: waituntilterminated; Check: NeedsWebView2
#endif
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
const
  WebView2ClientGuid = '{F3017226-FE2A-4295-8BDF-00C3A9C2BBED}';

function WebView2Installed(): Boolean;
var
  Version: string;
begin
  Result :=
    RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\' + WebView2ClientGuid, 'pv', Version) or
    RegQueryStringValue(HKLM, 'Software\Microsoft\EdgeUpdate\Clients\' + WebView2ClientGuid, 'pv', Version) or
    RegQueryStringValue(HKLM32, 'Software\Microsoft\EdgeUpdate\Clients\' + WebView2ClientGuid, 'pv', Version) or
    RegQueryStringValue(HKLM64, 'Software\Microsoft\EdgeUpdate\Clients\' + WebView2ClientGuid, 'pv', Version);
end;

function NeedsWebView2(): Boolean;
begin
  Result := not WebView2Installed();
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
#ifnexist WebView2Bootstrapper
  if NeedsWebView2() then
  begin
    MsgBox(
      'Microsoft Edge WebView2 Runtime does not appear to be installed.' + #13#10 + #13#10 +
      'The app needs WebView2 to display its desktop window. This installer was built without the WebView2 bootstrapper, so install WebView2 from Microsoft if the app window does not open.',
      mbInformation,
      MB_OK
    );
  end;
#endif
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ForceDirectories(ExpandConstant('{userappdata}\ValorantTracker'));
    ForceDirectories(ExpandConstant('{userappdata}\ValorantTracker\logs'));
    ForceDirectories(ExpandConstant('{userappdata}\ValorantTracker\cache'));
  end;
end;
