#!/usr/bin/perl

use strict;
use warnings;
use IO::Socket::INET;
use File::Basename;

my $port = 5000;
my $host = '0.0.0.0';
my $server = IO::Socket::INET->new(
    LocalHost => $host,
    LocalPort => $port,
    Proto => 'tcp',
    Listen => 5,
    Reuse => 1
) or die "Cannot create server on $host:$port: $!";

print "HTTP Server running at http://$host:$port/\n";

# Define content types for different file extensions
my %CONTENT_TYPES = (
    'html' => 'text/html',
    'js'   => 'application/javascript',
    'css'  => 'text/css',
    'json' => 'application/json',
    'png'  => 'image/png',
    'jpg'  => 'image/jpeg',
    'gif'  => 'image/gif',
    'svg'  => 'image/svg+xml',
    'ico'  => 'image/x-icon',
    'xlsx' => 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls'  => 'application/vnd.ms-excel',
);

# Make sure the uploads directory exists
unless (-d 'uploads') {
    mkdir 'uploads' or warn "Could not create directory 'uploads': $!";
}

# Main server loop
while (my $client = $server->accept()) {
    my $request = '';
    my $path = '';
    
    # Read the HTTP request
    while (my $line = <$client>) {
        $request .= $line;
        last if $line =~ /^\r?\n$/;
        
        # Extract the requested path
        if ($line =~ /^GET\s+\/([^\s]*)\s+HTTP/) {
            $path = $1;
        }
    }
    
    # Default to index.html if no path specified
    $path = 'index.html' if $path eq '';
    
    # Special handling for /list_files
    if ($path eq 'list_files') {
        my $asset_file = 'attached_assets/PILT Tables Workbook_2025.xlsx';
        my $json = '{
            "success": true,
            "files": [
                {
                    "filename": "PILT Tables Workbook_2025.xlsx",
                    "path": "' . $asset_file . '",
                    "source": "asset"
                }
            ]
        }';
        
        print $client "HTTP/1.1 200 OK\r\n";
        print $client "Content-Type: application/json\r\n";
        print $client "Content-Length: " . length($json) . "\r\n";
        print $client "Connection: close\r\n";
        print $client "Access-Control-Allow-Origin: *\r\n";
        print $client "\r\n";
        print $client $json;
        
        close $client;
        next;
    }
    
    # Special handling for /read_excel
    if ($path =~ /^read_excel\?file=(.+)$/) {
        my $file_path = $1;
        $file_path =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/eg; # URL decode
        
        # Check if file exists
        unless (-f $file_path) {
            my $error_json = '{
                "success": false,
                "message": "File not found: ' . $file_path . '"
            }';
            
            print $client "HTTP/1.1 404 Not Found\r\n";
            print $client "Content-Type: application/json\r\n";
            print $client "Content-Length: " . length($error_json) . "\r\n";
            print $client "Connection: close\r\n";
            print $client "Access-Control-Allow-Origin: *\r\n";
            print $client "\r\n";
            print $client $error_json;
            
            close $client;
            next;
        }
        
        # Read the file in binary mode
        my $file_content = '';
        if (open my $fh, '<:raw', $file_path) {
            binmode($fh);
            local $/;
            $file_content = <$fh>;
            close $fh;
        } else {
            my $error_json = '{
                "success": false,
                "message": "Error reading file: ' . $! . '"
            }';
            
            print $client "HTTP/1.1 500 Internal Server Error\r\n";
            print $client "Content-Type: application/json\r\n";
            print $client "Content-Length: " . length($error_json) . "\r\n";
            print $client "Connection: close\r\n";
            print $client "Access-Control-Allow-Origin: *\r\n";
            print $client "\r\n";
            print $client $error_json;
            
            close $client;
            next;
        }
        
        # Convert to base64
        my $encoded = '';
        for my $byte (split //, $file_content) {
            $encoded .= sprintf("%02X", ord($byte));
        }
        
        # Create a JSON response with the base64 data
        my $filename = basename($file_path);
        my $json = '{
            "success": true,
            "filename": "' . $filename . '",
            "data": "' . $encoded . '",
            "format": "hex"
        }';
        
        print $client "HTTP/1.1 200 OK\r\n";
        print $client "Content-Type: application/json\r\n";
        print $client "Content-Length: " . length($json) . "\r\n";
        print $client "Connection: close\r\n";
        print $client "Access-Control-Allow-Origin: *\r\n";
        print $client "\r\n";
        print $client $json;
        
        close $client;
        next;
    }
    
    my $content;
    my $content_type = 'text/plain';
    my $status = "200 OK";
    
    # Determine the file extension and corresponding content type
    if ($path =~ /\.(\w+)$/) {
        $content_type = $CONTENT_TYPES{$1} || 'text/plain';
    }
    
    # Try to open the requested file
    if (-f $path && open my $fh, '<', $path) {
        # Get the file content
        $content = do { local $/; <$fh> };
        close $fh;
        print "Serving $path with content-type: $content_type\n";
    } else {
        # If file doesn't exist, use a 404 response
        $status = "404 Not Found";
        if (open my $fh, '<', "404.html") {
            $content = do { local $/; <$fh> };
            close $fh;
            $content_type = 'text/html';
        } else {
            $content = "<html><body><h1>404 - Not Found</h1><p>The requested file $path was not found.</p></body></html>";
        }
        print "File not found: $path\n";
    }
    
    # Send the HTTP response
    print $client "HTTP/1.1 $status\r\n";
    print $client "Content-Type: $content_type\r\n";
    print $client "Content-Length: " . length($content) . "\r\n";
    print $client "Connection: close\r\n";
    print $client "Access-Control-Allow-Origin: *\r\n";
    print $client "\r\n";
    print $client $content;
    
    close $client;
}