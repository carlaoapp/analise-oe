using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Diagnostics;
using System.Reflection;
using System.Drawing;
using System.Windows.Forms;
using Microsoft.Win32;
using System.Web.Script.Serialization;
using System.Collections.Generic;

namespace PainelManutencaoDesktop
{
    public class Program
    {
        private static HttpListener _listener;
        private static int _port;
        private static NotifyIcon _trayIcon;
        private static Mutex _mutex;
        private static bool _isRunning = true;
        private static string _edgePath;

        private static string _dataFile = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data.json");
        private static string _uploadsDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "uploads");

        [STAThread]
        private static void Log(string msg)
        {
            try
            {
                string logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app_debug.log");
                File.AppendAllText(logPath, string.Format("[{0:yyyy-MM-dd HH:mm:ss.fff}] {1}\r\n", DateTime.Now, msg));
            }
            catch { }
        }

        [STAThread]
        public static void Main(string[] args)
        {
            AppDomain.CurrentDomain.UnhandledException += (s, e) => {
                Log(string.Format("UNHANDLED EXCEPTION: {0}", e.ExceptionObject));
            };
            Application.ThreadException += (s, e) => {
                Log(string.Format("THREAD EXCEPTION: {0}", e.Exception.Message));
            };
            AppDomain.CurrentDomain.ProcessExit += (s, e) => {
                Log(string.Format("PROCESS EXIT EVENT. Environment.ExitCode: {0}", Environment.ExitCode));
            };

            Log("=== Main Iniciando ===");
            bool createdNew;
            _mutex = new Mutex(true, "PainelManutencao_SingleInstance_App_Mutex", out createdNew);
            Log(string.Format("Mutex criado. createdNew: {0}", createdNew));

            if (!createdNew)
            {
                try
                {
                    string existingPort = File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "port.txt")).Trim();
                    OpenBrowser("http://localhost:" + existingPort + "/index.html");
                }
                catch { }
                return;
            }

            try
            {
                if (!Directory.Exists(_uploadsDir))
                {
                    Directory.CreateDirectory(_uploadsDir);
                }

                _port = FindFreePort();
                Log(string.Format("Porta livre encontrada: {0}", _port));
                File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "port.txt"), _port.ToString());

                StartServer(_port);
                Log("Servidor HTTP iniciado com sucesso.");

                _edgePath = FindEdgePath();
                Log(string.Format("Edge path: {0}", _edgePath));

                string url = "http://localhost:" + _port + "/index.html";
                OpenBrowser(url);

                SetupTrayIcon();
                Log("Iniciando Application.Run()...");
                Application.Run();
            }
            catch (Exception ex)
            {
                Log(string.Format("ERRO FATAL NA INICIALIZACAO: {0}\r\n{1}", ex.Message, ex.StackTrace));
                MessageBox.Show("Erro ao iniciar o Painel de Manutenção:\n" + ex.Message, "Painel de Manutenção", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                Log("=== Encerrando Execucao ===");
                _isRunning = false;
                if (_listener != null)
                {
                    try { _listener.Stop(); } catch { }
                }
                if (_trayIcon != null)
                {
                    _trayIcon.Visible = false;
                    _trayIcon.Dispose();
                }
                if (_mutex != null)
                {
                    try { _mutex.ReleaseMutex(); } catch { }
                    _mutex.Dispose();
                }
            }
        }

        private static int FindFreePort()
        {
            TcpListener l = new TcpListener(IPAddress.Loopback, 0);
            l.Start();
            int port = ((IPEndPoint)l.LocalEndpoint).Port;
            l.Stop();
            return port;
        }

        private static string GetLocalIPAddress()
        {
            try
            {
                using (Socket socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, 0))
                {
                    socket.Connect("8.8.8.8", 65530);
                    IPEndPoint endPoint = socket.LocalEndPoint as IPEndPoint;
                    if (endPoint != null) return endPoint.Address.ToString();
                }
            }
            catch { }

            try
            {
                var host = Dns.GetHostEntry(Dns.GetHostName());
                foreach (var ip in host.AddressList)
                {
                    if (ip.AddressFamily == AddressFamily.InterNetwork && !IPAddress.IsLoopback(ip))
                    {
                        return ip.ToString();
                    }
                }
            }
            catch { }

            return "127.0.0.1";
        }

        private static void StartServer(int port)
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add("http://localhost:" + port + "/");
            _listener.Prefixes.Add("http://127.0.0.1:" + port + "/");
            _listener.Start();

            Thread serverThread = new Thread(() =>
            {
                while (_isRunning)
                {
                    try
                    {
                        HttpListenerContext context = _listener.GetContext();
                        ThreadPool.QueueUserWorkItem((ctx) => HandleRequest((HttpListenerContext)ctx), context);
                    }
                    catch (HttpListenerException) { break; }
                    catch (Exception ex)
                    {
                        Log(string.Format("Erro no loop do servidor: {0}", ex.Message));
                    }
                }
            });
            serverThread.IsBackground = true;
            serverThread.Start();
        }

        private static void HandleRequest(HttpListenerContext context)
        {
            HttpListenerRequest req = context.Request;
            HttpListenerResponse res = context.Response;

            res.Headers.Add("Access-Control-Allow-Origin", "*");
            res.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            res.Headers.Add("Access-Control-Allow-Headers", "Content-Type");

            if (req.HttpMethod == "OPTIONS")
            {
                res.StatusCode = 200;
                res.Close();
                return;
            }

            string rawUrl = req.Url.AbsolutePath;
            Log(string.Format("HTTP {0} {1}", req.HttpMethod, rawUrl));

            try
            {
                if (rawUrl == "/" || rawUrl == "")
                {
                    rawUrl = "/index.html";
                }

                if (rawUrl == "/api/ip" && req.HttpMethod == "GET")
                {
                    string json = "{\"ip\":\"" + GetLocalIPAddress() + "\",\"port\":" + _port + "}";
                    byte[] data = Encoding.UTF8.GetBytes(json);
                    res.ContentType = "application/json";
                    res.ContentLength64 = data.Length;
                    res.OutputStream.Write(data, 0, data.Length);
                    res.Close();
                    return;
                }

                // /api/criticas is an alias for /api/data (backwards compatibility)
                if (rawUrl == "/api/criticas" || rawUrl == "/api/criticas/")
                {
                    rawUrl = "/api/data";
                }

                if (rawUrl == "/api/status" && req.HttpMethod == "GET")
                {
                    string json = "{\"status\":\"online\",\"server\":\"Painel de Manutencao\",\"version\":\"2.0\",\"port\":" + _port + "}";
                    byte[] data = Encoding.UTF8.GetBytes(json);
                    res.ContentType = "application/json";
                    res.ContentLength64 = data.Length;
                    res.OutputStream.Write(data, 0, data.Length);
                    res.Close();
                    return;
                }

                if (rawUrl == "/api/sync/all" && req.HttpMethod == "POST")
                {
                    using (var reader = new StreamReader(req.InputStream, req.ContentEncoding))
                    {
                        string body = reader.ReadToEnd();
                        string backupPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "sync_backup_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".json");
                        File.WriteAllText(backupPath, body, Encoding.UTF8);
                    }
                    string json = "{\"success\":true,\"message\":\"Dados sincronizados com sucesso!\"}";
                    byte[] data = Encoding.UTF8.GetBytes(json);
                    res.ContentType = "application/json";
                    res.ContentLength64 = data.Length;
                    res.OutputStream.Write(data, 0, data.Length);
                    res.Close();
                    return;
                }

                if (rawUrl == "/api/data")
                {
                    if (req.HttpMethod == "GET")
                    {
                        if (File.Exists(_dataFile))
                        {
                            byte[] data = File.ReadAllBytes(_dataFile);
                            res.ContentType = "application/json";
                            res.ContentLength64 = data.Length;
                            res.OutputStream.Write(data, 0, data.Length);
                        }
                        else
                        {
                            byte[] data = Encoding.UTF8.GetBytes("[]");
                            res.ContentType = "application/json";
                            res.ContentLength64 = data.Length;
                            res.OutputStream.Write(data, 0, data.Length);
                        }
                        res.Close();
                        return;
                    }
                    else if (req.HttpMethod == "POST")
                    {
                        using (var reader = new StreamReader(req.InputStream, req.ContentEncoding))
                        {
                            string body = reader.ReadToEnd();
                            File.WriteAllText(_dataFile, body, Encoding.UTF8);
                        }
                        byte[] data = Encoding.UTF8.GetBytes("{\"success\":true}");
                        res.ContentType = "application/json";
                        res.ContentLength64 = data.Length;
                        res.OutputStream.Write(data, 0, data.Length);
                        res.Close();
                        return;
                    }
                }

                // Serve static files from embedded resources or local public/ folder
                string relativePath = rawUrl.TrimStart('/');
                string localFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "public", relativePath.Replace('/', '\\'));

                if (File.Exists(localFilePath))
                {
                    byte[] fileBytes = File.ReadAllBytes(localFilePath);
                    res.ContentType = GetMimeType(Path.GetExtension(localFilePath));
                    res.ContentLength64 = fileBytes.Length;
                    res.OutputStream.Write(fileBytes, 0, fileBytes.Length);
                    res.Close();
                    return;
                }

                // Try embedded resource
                string resourceName = "public." + relativePath.Replace('/', '.').Replace('\\', '.');
                var asm = Assembly.GetExecutingAssembly();
                using (Stream stream = asm.GetManifestResourceStream(resourceName))
                {
                    if (stream != null)
                    {
                        byte[] buffer = new byte[stream.Length];
                        stream.Read(buffer, 0, buffer.Length);
                        res.ContentType = GetMimeType(Path.GetExtension(relativePath));
                        res.ContentLength64 = buffer.Length;
                        res.OutputStream.Write(buffer, 0, buffer.Length);
                        res.Close();
                        return;
                    }
                }

                res.StatusCode = 404;
                byte[] notFound = Encoding.UTF8.GetBytes("404 Not Found");
                res.OutputStream.Write(notFound, 0, notFound.Length);
                res.Close();
            }
            catch (Exception ex)
            {
                Log(string.Format("Erro na requisicao {0}: {1}", rawUrl, ex.Message));
                try
                {
                    res.StatusCode = 500;
                    res.Close();
                }
                catch { }
            }
        }

        private static string GetMimeType(string ext)
        {
            if (string.IsNullOrEmpty(ext)) return "application/octet-stream";
            switch (ext.ToLower())
            {
                case ".html": return "text/html; charset=utf-8";
                case ".css": return "text/css; charset=utf-8";
                case ".js": return "application/javascript; charset=utf-8";
                case ".json": return "application/json; charset=utf-8";
                case ".png": return "image/png";
                case ".jpg":
                case ".jpeg": return "image/jpeg";
                case ".gif": return "image/gif";
                case ".svg": return "image/svg+xml";
                case ".ico": return "image/x-icon";
                default: return "application/octet-stream";
            }
        }

        private static void SetupTrayIcon()
        {
            _trayIcon = new NotifyIcon();
            _trayIcon.Text = "Painel de Manutenção";
            
            try
            {
                string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "public", "favicon.ico");
                if (File.Exists(iconPath))
                {
                    _trayIcon.Icon = new Icon(iconPath);
                }
                else
                {
                    _trayIcon.Icon = SystemIcons.Application;
                }
            }
            catch
            {
                _trayIcon.Icon = SystemIcons.Application;
            }

            ContextMenu menu = new ContextMenu();
            menu.MenuItems.Add("Abrir Painel de Manutenção", (s, e) => {
                OpenBrowser("http://localhost:" + _port + "/index.html");
            });
            menu.MenuItems.Add("Abrir Nova Crítica", (s, e) => {
                OpenBrowser("http://localhost:" + _port + "/desktop/nova.html");
            });
            menu.MenuItems.Add("Abrir OS em Campo", (s, e) => {
                OpenBrowser("http://localhost:" + _port + "/desktop/os.html");
            });
            menu.MenuItems.Add("Abrir Check list Entrada", (s, e) => {
                OpenBrowser("http://localhost:" + _port + "/desktop/checkin.html");
            });
            menu.MenuItems.Add("Abrir Check list Saída", (s, e) => {
                OpenBrowser("http://localhost:" + _port + "/desktop/checkout.html");
            });
            menu.MenuItems.Add("-");
            menu.MenuItems.Add("Sair", (s, e) => {
                _isRunning = false;
                Application.Exit();
            });

            _trayIcon.ContextMenu = menu;
            _trayIcon.DoubleClick += (s, e) => {
                OpenBrowser("http://localhost:" + _port + "/index.html");
            };
            _trayIcon.Visible = true;
        }

        private static string FindEdgePath()
        {
            string[] paths = {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Microsoft\\Edge\\Application\\msedge.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Microsoft\\Edge\\Application\\msedge.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Microsoft\\Edge\\Application\\msedge.exe")
            };

            foreach (var p in paths)
            {
                if (File.Exists(p)) return p;
            }
            return null;
        }

        private static void OpenBrowser(string url)
        {
            try
            {
                if (!string.IsNullOrEmpty(_edgePath) && File.Exists(_edgePath))
                {
                    string profileDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "edge_profile");
                    string args = string.Format("--app=\"{0}\" --user-data-dir=\"{1}\" --no-first-run --no-default-browser-check", url, profileDir);
                    Process.Start(_edgePath, args);
                    return;
                }
            }
            catch (Exception ex)
            {
                Log(string.Format("Falha ao abrir modo app Edge: {0}", ex.Message));
            }

            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                Log(string.Format("Falha ao abrir navegador padrao: {0}", ex.Message));
            }
        }
    }
}
