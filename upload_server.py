#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import cgi
import tempfile
import base64
from urllib.parse import parse_qs, urlparse

# Define the port
PORT = 5000

class PILTRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Serve GET requests"""
        # Special case for the /list_files endpoint
        if self.path.startswith('/list_files'):
            self.list_files()
            return
        
        # Special case for the /read_excel endpoint
        if self.path.startswith('/read_excel'):
            self.read_excel()
            return
            
        # Default file serving behavior
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        """Handle POST requests for file uploads"""
        if self.path == '/upload':
            self.handle_upload()
            return
            
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'404 Not Found')
    
    def handle_upload(self):
        """Handle file upload"""
        try:
            # Parse the form data
            content_type, pdict = cgi.parse_header(self.headers['Content-Type'])
            
            if content_type == 'multipart/form-data':
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # Get the file data
                if 'file' in form:
                    fileitem = form['file']
                    if fileitem.filename:
                        # Save the file
                        file_path = os.path.join('uploads', fileitem.filename)
                        os.makedirs('uploads', exist_ok=True)
                        
                        with open(file_path, 'wb') as f:
                            f.write(fileitem.file.read())
                        
                        # Respond with success
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        response = {
                            'success': True,
                            'message': f'File {fileitem.filename} uploaded successfully',
                            'filename': fileitem.filename
                        }
                        self.wfile.write(json.dumps(response).encode())
                        return
            
            # If we get here, something went wrong
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': False,
                'message': 'No file received or invalid request'
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': False,
                'message': f'Server error: {str(e)}'
            }
            self.wfile.write(json.dumps(response).encode())
    
    def list_files(self):
        """List Excel files in the uploads directory and attached_assets directory"""
        try:
            files = []
            
            # List files in uploads directory
            if os.path.exists('uploads'):
                for filename in os.listdir('uploads'):
                    if filename.endswith('.xlsx') or filename.endswith('.xls'):
                        files.append({
                            'filename': filename,
                            'path': os.path.join('uploads', filename),
                            'source': 'uploaded'
                        })
            
            # List files in attached_assets directory
            if os.path.exists('attached_assets'):
                for filename in os.listdir('attached_assets'):
                    if filename.endswith('.xlsx') or filename.endswith('.xls'):
                        files.append({
                            'filename': filename,
                            'path': os.path.join('attached_assets', filename),
                            'source': 'asset'
                        })
                        
            # List sample files in the main directory
            for filename in os.listdir('.'):
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    files.append({
                        'filename': filename,
                        'path': filename,
                        'source': 'sample'
                    })
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'files': files
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': False,
                'message': f'Server error: {str(e)}'
            }
            self.wfile.write(json.dumps(response).encode())
            
    def read_excel(self):
        """Read Excel file data and return it as JSON"""
        try:
            # Parse query parameters
            query = urlparse(self.path).query
            params = parse_qs(query)
            
            if 'file' not in params:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    'success': False,
                    'message': 'No file parameter provided'
                }
                self.wfile.write(json.dumps(response).encode())
                return
                
            filepath = params['file'][0]
            
            # Check if the file exists
            if not os.path.exists(filepath):
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    'success': False,
                    'message': f'File not found: {filepath}'
                }
                self.wfile.write(json.dumps(response).encode())
                return
                
            # Simple extraction of data using the file extension
            if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
                # Convert the file to base64 to send to the client for processing
                with open(filepath, 'rb') as f:
                    file_data = base64.b64encode(f.read()).decode('utf-8')
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    'success': True,
                    'filename': os.path.basename(filepath),
                    'data': file_data,
                    'format': 'base64'
                }
                self.wfile.write(json.dumps(response).encode())
                return
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    'success': False,
                    'message': 'Unsupported file format. Only Excel files (.xlsx, .xls) are supported.'
                }
                self.wfile.write(json.dumps(response).encode())
                return
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': False,
                'message': f'Server error: {str(e)}'
            }
            self.wfile.write(json.dumps(response).encode())

def run():
    """Run the HTTP server"""
    handler = PILTRequestHandler
    
    # Ensure directory exists for uploads
    os.makedirs('uploads', exist_ok=True)
    
    # Create and start server
    with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
        print(f"Server running at http://0.0.0.0:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run()