#!/usr/bin/env python3
import http.server
import socketserver

PORT = 5000
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving at 0.0.0.0:{PORT}")
    httpd.serve_forever()