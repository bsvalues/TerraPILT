#!/usr/bin/perl

use strict;
use warnings;
use IO::Socket::INET;

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

while (my $client = $server->accept()) {
    my $request = '';
    while (<$client>) {
        $request .= $_;
        last if /^\r?\n$/;
    }
    
    # Simple HTTP response with index.html content
    open my $fh, '<', 'index.html' or die "Can't open index.html: $!";
    my $content = do { local $/; <$fh> };
    close $fh;
    
    print $client "HTTP/1.1 200 OK\r\n";
    print $client "Content-Type: text/html\r\n";
    print $client "Content-Length: " . length($content) . "\r\n";
    print $client "Connection: close\r\n";
    print $client "\r\n";
    print $client $content;
    
    close $client;
}