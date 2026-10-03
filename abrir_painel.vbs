Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim srvPath, pythonPath, chromePath
srvPath = "c:\Desenvolvimento\Projetos\Analise O.E\servidor.py"
pythonPath = "C:\Users\NOTE\AppData\Local\Programs\Python\Python311\pythonw.exe"

' Localiza Chrome ou Edge
chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
If Not fso.FileExists(chromePath) Then
    chromePath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
End If
If Not fso.FileExists(chromePath) Then
    chromePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
End If
If Not fso.FileExists(chromePath) Then
    chromePath = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
End If

' Verifica se o servidor Python ja esta rodando na porta 8000
On Error Resume Next
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
http.setTimeouts 800, 800, 800, 800
http.Open "GET", "http://127.0.0.1:8000/api/ip", False
http.Send

If Err.Number <> 0 Or http.Status <> 200 Then
    ' Servidor nao estava rodando: inicia silenciosamente com pythonw
    If fso.FileExists(pythonPath) Then
        WshShell.Run """" & pythonPath & """ """ & srvPath & """", 0, False
    Else
        WshShell.Run "python """ & srvPath & """", 0, False
    End If
    WScript.Sleep 1200
End If
On Error GoTo 0

' Abre o Painel Desktop em modo App Nativo
WshShell.Run """" & chromePath & """ --app=http://localhost:8000/ --window-size=1280,820", 1, False