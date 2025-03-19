#!/usr/bin/env python
"""
Simple HTTP Server for PILT Dashboard
"""
import http.server
import socketserver

PORT = 5000
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

Handler.extensions_map = {
    '.html': 'text/html',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '': 'application/octet-stream',
}

def run_server():
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Server started at http://0.0.0.0:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()