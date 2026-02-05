from http.server import BaseHTTPRequestHandler, HTTPServer
import socket

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Hello World from WSL!</h1></body></html>")

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def run(server_class=HTTPServer, handler_class=SimpleHandler, port=4444):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    
    print(f"Starting server on port {port}...")
    print(f"Try connecting from another device using: http://{get_ip_address()}:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
