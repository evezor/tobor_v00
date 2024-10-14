from websocket import websocket
import uselect
import uasyncio as asyncio
import os, json, socket, network, sys, io
from time import sleep
from iris import Iris
try:
    import usys as sys
except ImportError:
    import sys

try:
    import ubinascii as binascii
except:
    import binascii
try:
    import uhashlib as hashlib
except:
    import hashlib
import gc

#######################
# repl
#######################

def do_repl(code: str, iris):
    print('repling', code)
    code.replace('<br>', '\n')
    code.replace('&nbsp;', ' ')
    try:
            _return = str(eval(code, globals(), iris.locals)).strip('<>')
            return f">>> {code}\n{_return}"

    except SyntaxError:
        try:
            exec(compile(code, 'input', 'single'), globals(), iris.locals)

            return f">>> {code}"
        except Exception as e:
            return f">>> {code}\n{e}"


    except Exception as e:
        print(e)
        thing = io.StringIO()
        sys.print_exception(e, thing)
        print(thing.getvalue())
        exc = thing.getvalue().replace('\n', '<br>')
        return f">>> {code}\n{exc}"


#######################
# websocket_helper
#######################
DEBUG = 0

def server_handshake(sock):
    clr = sock.makefile("rwb", 0)
    l = clr.readline()
    # sys.stdout.write(repr(l))

    webkey = None

    while 1:
        l = clr.readline()
        if not l:
            raise OSError("EOF in headers")
        if l == b"\r\n":
            break
        #    sys.stdout.write(l)
        h, v = [x.strip() for x in l.split(b":", 1)]
        if DEBUG:
            print((h, v))
        if h == b"Sec-WebSocket-Key":
            webkey = v

    if not webkey:
        raise OSError("Not a websocket request")

    if DEBUG:
        print("Sec-WebSocket-Key:", webkey, len(webkey))

    d = hashlib.sha1(webkey)
    d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    respkey = d.digest()
    respkey = binascii.b2a_base64(respkey)[:-1]
    if DEBUG:
        print("respkey:", respkey)

    sock.send(
        b"""\
HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: """
    )
    sock.send(respkey)
    sock.send("\r\n\r\n")


# Very simplified client handshake, works for MicroPython's
# websocket server implementation, but probably not for other
# servers.
def client_handshake(sock):
    cl = sock.makefile("rwb", 0)
    cl.write(
        b"""\
GET / HTTP/1.1\r
Host: echo.websocket.org\r
Connection: Upgrade\r
Upgrade: websocket\r
Sec-WebSocket-Key: foo\r
\r
"""
    )
    l = cl.readline()
    #    print(l)
    while 1:
        l = cl.readline()
        if l == b"\r\n":
            break


#        sys.stdout.write(l)

#######################
# ws_server
#######################

class WebSocketClient:
    def __init__(self, conn):
        self.connection = conn

    def process(self):
        pass


class WebSocketServer:
    def __init__(self, page, max_connections=1):
        self._listen_s = None
        self._listen_poll = None
        self._clients = []
        self._max_connections = max_connections
        self._page = page

    def _setup_conn(self, port):
        self._listen_s = socket.socket()
        self._listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listen_poll = uselect.poll()

        ai = socket.getaddrinfo("0.0.0.0", port)
        addr = ai[0][4]

        self._listen_s.bind(addr)
        self._listen_s.listen(1)
        self._listen_poll.register(self._listen_s)
        for i in (network.AP_IF, network.STA_IF):
            iface = network.WLAN(i)
            if iface.active():
                print("WebSocket started on ws://%s:%d" % (iface.ifconfig()[0], port))

    def _check_new_connections(self, accept_handler):
        poll_events = self._listen_poll.poll(0)
        if not poll_events:
            return
        
        # print(poll_events)
        if poll_events[0][1] & uselect.POLLIN:
            accept_handler(poll_events[0][0])

    def _accept_conn(self):
        cl, remote_addr = self._listen_s.accept()
        print("Client connection from:", remote_addr)

        if len(self._clients) >= self._max_connections:
            # Maximum connections limit reached
            cl.setblocking(True)
            cl.sendall("HTTP/1.1 503 Too many connections\n\n")
            cl.sendall("\n")
            #TODO: Make sure the data is sent before closing
            sleep(0.1)
            cl.close()
            return

        try:
            server_handshake(cl)
        except OSError:
            # Not a websocket connection, serve webpage
            self._serve_page(cl)
            return

        client = self._make_client(WebSocketConnection(remote_addr, cl, self.remove_connection))
        self._clients.append(client)

    def _make_client(self, conn):
        return WebSocketClient(conn)

    def _serve_page(self, sock):
        try:
            sock.sendall('HTTP/1.1 200 OK\nConnection: close\nServer: WebSocket Server\nContent-Type: text/html\n')
            length = os.stat(self._page)[6]
            sock.sendall('Content-Length: {}\n\n'.format(length))
            # Process page by lines to avoid large strings
            with open(self._page, 'r') as f:
                for line in f:
                    sock.sendall(line)
        except OSError:
            # Error while serving webpage
            pass
        sock.close()

    def stop(self):
        if self._listen_poll:
            self._listen_poll.unregister(self._listen_s)
        self._listen_poll = None
        if self._listen_s:
            self._listen_s.close()
        self._listen_s = None

        for client in self._clients:
            client.connection.close()
        print("Stopped WebSocket server.")

    def start(self, port=80):
        if self._listen_s:
            self.stop()
        self._setup_conn(port)
        print("Started WebSocket server.")

    def process_all(self):
        self._check_new_connections(self._accept_conn)

        for client in self._clients:
            client.process()

    def remove_connection(self, conn):
        for client in self._clients:
            if client.connection is conn:
                self._clients.remove(client)
                return

#######################
# ws connection
#######################

class ClientClosedError(Exception):
    pass


class WebSocketConnection:
    def __init__(self, addr, s, close_callback):
        self.client_close = False
        self._need_check = False

        self.address = addr
        self.socket = s
        self.ws = websocket(s, True)
        self.poll = uselect.poll()
        self.close_callback = close_callback

        self.socket.setblocking(False)
        self.poll.register(self.socket, uselect.POLLIN)

    def read(self):
        poll_events = self.poll.poll(0)

        if not poll_events:
            return

        # Check the flag for connection hung up
        if poll_events[0][1] & uselect.POLLHUP:
            self.client_close = True

        msg_bytes = None
        try:
            msg_bytes = self.ws.read()
        except OSError:
            self.client_close = True

        # If no bytes => connection closed. See the link below.
        # http://stefan.buettcher.org/cs/conn_closed.html
        if not msg_bytes or self.client_close:
            raise ClientClosedError()

        return msg_bytes

    def write(self, msg):
        try:
            self.ws.write(msg)
        except OSError:
            self.client_close = True

    def is_closed(self):
        return self.socket is None

    def close(self):
        print("Closing connection.")
        self.poll.unregister(self.socket)
        self.socket.close()
        self.socket = None
        self.ws = None
        if self.close_callback:
            self.close_callback(self)


#######################
# ws_multiserver
#######################

class WebSocketMultiServer(WebSocketServer):
    http_codes = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error",
        503: "Service Unavailable"
    }

    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "html": "text/html",
        "htm": "text/html",
        "css": "text/css",
        "js": "application/javascript"
    }

    def __init__(self, index_page, max_connections, pages):
        super().__init__(index_page, max_connections)
        dir_idx = index_page.rfind("/")
        self._web_dir = index_page[0:dir_idx] + '/' if dir_idx > 0 else "/"
        self._pages = pages
        print(self._pages)

    def _accept_conn(self, listen_sock):
        cl, remote_addr = listen_sock.accept()
        # print("Client connection from:", remote_addr)

        if len(self._clients) >= self._max_connections:
            # Maximum connections limit reached
            cl.setblocking(True)
            self._generate_static_page(cl, 503, "503 Too Many Connections")
            return

        requested_file = None
        data = cl.recv(128).decode()
        if not data:
            cl.close()
            return
        
        if data and "Upgrade: websocket" not in data.split("\r\n") and "GET" == data.split(" ")[0]:
            # data should looks like GET /index.html HTTP/1.1\r\nHost: 19"
            # requested file is on second position in data, ignore all get parameters after question mark
            requested_file = data.split(" ")[1].split("?")[0]
            requested_file = self._pages[requested_file] if requested_file in self._pages else requested_file
            # print(requested_file)
        try:
            server_handshake(cl)
            self._clients.append(self._make_client(WebSocketConnection(remote_addr, cl, self.remove_connection)))
        except OSError:
            if requested_file:
                cl.setblocking(True)
                self._serve_file(requested_file, cl)
            else:
                self._generate_static_page(cl, 500, "500 Internal Server Error [2]")

    def _serve_file(self, requested_file, c_socket):
        print(f"### Serving file: {requested_file}")
        try:
            # check if file exists in web directory
            path = requested_file.split("/")
            filename = path[-1]
            subdir = "/" + "/".join(path[1:-1]) if len(path) > 2 else ""
            if filename not in os.listdir(self._web_dir + subdir):
                self._generate_static_page(c_socket, 404, "404 Not Found")
                return

            # Create path based on web root directory
            file_path = self._web_dir + requested_file
            length = os.stat(file_path)[6]
            c_socket.sendall(self._generate_headers(200, file_path, length))
            # Send file by chunks to prevent large memory consumption
            chunk_size = 768
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    c_socket.sendall(data)
                    if len(data) < chunk_size:
                        break
            sleep(0.1)
            c_socket.close()
        except OSError:
            self._generate_static_page(c_socket, 500, "500 Internal Server Error [2]")

    @staticmethod
    def _generate_headers(code, filename=None, length=None):
        content_type = "text/html"

        if filename:
            ext = filename.split(".")[1]
            if ext in WebSocketMultiServer.mime_types:
                content_type = WebSocketMultiServer.mime_types[ext]

        # Close connection after completing the request
        return "HTTP/1.1 {} {}\n" \
               "Content-Type: {}\n" \
               "Content-Length: {}\n" \
               "Server: ESPServer\n" \
               "Connection: close\n\n".format(
                code, WebSocketMultiServer.http_codes[code], content_type, length)

    @staticmethod
    def _generate_static_page(sock, code, message):
        sock.sendall(WebSocketMultiServer._generate_headers(code))
        sock.sendall("<html><body><h1>" + message + "</h1></body></html>")
        print('should there be a sleep here???')
        sleep(0.5)
        sock.close()


#######################
# main
#######################

class Client(WebSocketClient):
    def __init__(self, conn, iris):
        super().__init__(conn)
        self.iris = iris
        self.filename = None
        self.file = None
        
    def open_file(self, filename):
        self.filename = filename.decode()
        self.file = open('temp', 'wb')
    
    def close_file(self):
        self.file.close()
        self.file = None
        os.rename('temp', self.filename)
        self.filename = None
        
    def process(self):
        # Process WEBSOCKET Data
        try:
            msg = self.connection.read()
            if not msg:  # we will send messages out when there are no new messages in
                if self.iris.bifrost.any():
                    line = self.iris.bifrost.pop()
                    self.connection.write(line)
                return
            # print(msg)
            if msg == b'get_webstuff':
                self.connection.write(f'compose_page,{self.iris.get_gui()}')
                return
            
                
            
            
            ##PID##,$$DATA$$ <- message format
            comma = msg.find(b',')
            if comma == -1:
                return f'unknwn thing from socket {msg}'
            pid = msg[:comma]
            data = msg[comma+1:]
            
            
            if pid == b'term':
                code = data.decode("utf-8")
                self.connection.write(f'term,{do_repl(code, self.iris)}')
                return
            
            
            # -------
            #  Filesender Stuff
            # -------
            elif pid == b'get_file':
                gc.collect()
                data = data.decode()
                with open(data, 'r') as f:
                    try:
                        self.connection.write(f'to_file_editor,{data},{f.read()}')
                    except MemoryError:
                        self.connection.write(f'to_file_editor,error,Memory allocation Error\nfile is too large')
                return
            elif pid == b'save_file':
                if data[:9] == b'newsingle':
                    second_comma = data.find(b',', 10)
                    filename = data[10:second_comma]
                    print(filename)
                    self.open_file(filename)
                    print('isnewsingle')
                    self.file.write(data[second_comma+1:])
                    self.close_file()
                elif data[:3] == b'new':
                    second_comma = data.find(b',', 4)    
                    filename = data[4:second_comma]
                    print(filename)
                    self.open_file(filename)
                    print('isnew')
                    self.file.write(data[second_comma+1:])
                    self.connection.write(f'send_next_chunk, ')
                elif data[:3] == b'end':
                    print('end')
                    self.file.write(data[4:])
                    self.close_file()
                else: 
                    # assumed tag is 'chunk'
                    print('chunk')
                    self.file.write(data[6:])
                    self.connection.write(f'send_next_chunk, ')
                return
            
            elif pid == b'listdir':
                files = [file[0] for file in os.ilistdir() if file[1] == 32768]
                if 'sd' in os.listdir():
                    files.extend([f'sd/{file}' for file in os.listdir('sd')])
                files = json.dumps({'cmd': 'listdir', 'data': files})
                self.connection.write(f'listdir,{files}')
                return
            # -------
            #  <end> Filesender Stuff
            # -------
            
            pid = int(pid.decode("utf-8"))
            if data == b'true':
                data = True
            if data == b'false':
                data = False
            
            # try:
            print('processing', pid, data)
            self.iris.p[pid](data, gui=True)
            # except Exception as e:
            #     print('exception', e)

        except ClientClosedError:
            self.connection.close()
   

class WebsocketServer(WebSocketMultiServer):
    def __init__(self, *,
                 iris: Iris,
                 homepage: str = "static/terminal.html", 
                 simultanious_conns: int = 1, 
                 pages: dict[str, str]= {"/": "terminal.html", "/about": "about.html"}, 
                 **k):
        gc.collect()
        super().__init__(homepage, simultanious_conns, pages)
        
        # print('clients!!!', self._clients)
        
        self.iris = iris
        self.iris.bifrost._checked = self._clients
        iris.p[-1] = self
        self.start()
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk()) 
    
    def update(self):
        pass
    
    def gui(self):
        pass
                    
    async def chk(self):
        while True:
            self.process_all()
            await asyncio.sleep_ms(0)

    def _make_client(self, conn):
        return Client(conn, self.iris)




    