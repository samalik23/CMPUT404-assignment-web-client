#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

# Server sends a response to the client such as: HTTP/1.1 CODE RESPONSE HEADER

class HTTPClient(object):
    #def get_host_port(self,url):
    
    # Connect to socket
    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return self.socket
    
  
    def get_code(self, data):
        if not data:
            return
        # returns code from request by splitting data by space and grabbing the second index
        # Converted to float and int to avoid ValueError
        # Reference: https://stackoverflow.com/questions/1841565/valueerror-invalid-literal-for-int-with-base-10
        code = int(float(data.split(" ")[1]))
        return code

    # Obtain headers from response
    def get_headers(self,data):
        if not data:
            return
        return data.split("\r\n\r\n")[0]

    # Obtain body from response
    def get_body(self, data):
        if not data:
            return
        body = data.split("\r\n\r\n")
        # If the length of the body is greater than 1 then return the second index
        if (len(body) > 1):
            return body[1]
        # Otherwise just return body
        return body


    def sendall(self, data):
        if not data:
            return
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # A function to get information from the parsed URL
    # Also checks the validity of the hostname, port & path
    def get_parsed(self, url, body):

        # Parsing url here and obtaining information from that
        parsed_url = urllib.parse.urlparse(url)
        port = parsed_url.port
        hostname = parsed_url.hostname
        path = parsed_url.path

        # If we do not have a hostname, return a 400 code response
        if hostname == None:
            return HTTPResponse(400, body)

        # If we do not have a path or it is empty then make path = "/"
        if path == None or path == "":
            path = '/'

        # If we have no port, give a default value
        if port == None:
            if parsed_url.scheme == "http":
                port = 80
            elif parsed_url.scheme == "https":
                port = 443 

        # Information returned so other functions can utilize the data
        return parsed_url, port, hostname, path
    

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        code = 500
        body = ""

        # Parse URL & information 
        parsed_url, port, hostname, path = self.get_parsed(url, body)

        # Connect hostname and port to socket
        self.connect(hostname, port)

        # Establish the request message
        request = f"GET {path} HTTP/1.1\r\nHost: {hostname}\r\nAccept: */*\r\nConnection: close\r\n\r\n"

        # Send the request
        self.sendall(request)
        
        # Obtain the response from the webserver
        response = self.recvall(self.socket)

        # If we get no response, we can assume page does not exist
        if response == None:
            return HTTPResponse(404, body)
        
        # Otherwise, obtain the body and code from getter functions
        body = self.get_body(response)
        code = self.get_code(response)
        
        # Close the socket connection
        self.close()

        # Return a response with the given code and body
        return HTTPResponse(code, body)

    

    def POST(self, url, args=None):
        code = 500
        body = ""

        # Obtaining parsed and relevant information
        parsed_url, port, hostname, path = self.get_parsed(url, body)

        # Connect the hostname and port to the webserver
        self.connect(hostname, port)
        
        # If we have no arguments, we have no arguments to send
        if not args: 
            request_body = ""
            content_length = "0"
            content_type = ""

        # If we have arguments, parse the request body, obtain the length of content and define the type of content we are sending
        elif args:
            request_body = urllib.parse.urlencode(args, doseq=True)
            content_length = str(len(request_body))
            content_type = "application/x-www-form-urlencoded"

        # Establish the request message
        request = f"POST {path} HTTP/1.1\r\nHost: {hostname}:{port}\r\nAccept: */*\r\n \
                        Connection: Closed\r\nContent-Length: {content_length}\r\nContent-Type: {content_type}'\r\n\r\n{request_body}"
        
        # Send the request to the webserver
        self.sendall(request)

        # Obtain response from the webserver
        response = self.recvall(self.socket)

        # If we obtain no response, we can assume page does not exist
        if response == None:
            return HTTPResponse(404, body)

        # Otherwise obtain the body and code
        body = self.get_body(response)
        code = self.get_code(response)

        # Close the connection
        self.close()

        # Return a response with the given code and body
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
