#!/usr/bin/env python3

import socket
import selectors
import sys
import os 

from file_reader import FileReader

class Jewel:
    def __init__(self, port, file_path, file_reader):
        self.file_path = file_path

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", port))
        s.listen(5)
        s.setblocking(False)
        sel.register(s, selectors.EVENT_READ, Jewel.accept_wrapper)

        while True:
            e = sel.select()
            for x,_ in e:
                x.data(x.fileobj)

    def accept_wrapper(sock):
        (client, address) = sock.accept()
        print("[CONN] Connection from", address[0], "on port", address[1])
        client.setblocking(False)
        sel.register(client, selectors.EVENT_READ, Jewel.decode_wrapper)

    def decode_wrapper(client):
        address = client.getpeername()
        data = client.recv(1024)
        if not data:
            sel.unregister(client)
            client.close()
            return
        
        req  = decode_request(data, address)

        if not req:
            print(f"[ERRO] [{address[0]}:{address[1]}] unknown request returned error 400")
            header = 'HTTP/1.1 400 Bad Request\r\n'+'Connection: Closed\r\n\r\n'
            client.send(header.encode())
            client.close()
            sel.unregister(client)
            return
        
        [request_type, path, cookies] = req
            
        [header, content] = form_response(request_type, file_path+path.decode(), cookies, address)

        client.send(header.encode())

        if content:
            client.send(content)

        client.close()
        sel.unregister(client)

def decode_request(data, address):
    header_end = data.find(b'\r\n\r\n')
    if header_end > -1:
        header_string = data[:header_end]
        lines = header_string.split(b'\r\n')

        request_fields = lines[0].split()
        if not(len(request_fields) == 3):
            return None
        headers = lines[1:]
        # if len(headers) == 0:
        #     return None

        print(f"[REQU] [{address[0]}:{address[1]}] {request_fields[0].decode()} for {request_fields[1].decode()}")

        temp = []
        cookies = None;
        for header in headers:
            header_fields = header.split(b':')
            key = header_fields[0].strip()
            val = header_fields[1].strip()
            temp.append([key, val])
            if key==b'Cookie':
                cookies = val

        # look for certain character(series of character delinating something) /r/n/r/n
        # other way is length, look for that many bytes 
        data = None
       
        return [request_fields[0], request_fields[1], cookies]
    return None
    
def form_response(request_type, file_path, cookies, address):

    file_reader = FileReader()
    err = None
    data = None
    header = None
    direc = False
    if request_type == b'GET' or request_type == b'HEAD':
        data = file_reader.get(file_path, cookies)
        if not data:
            if os.path.isdir(file_path):
                direc = True
                data = "<html><body><h1>" + str(file_path) + "</h1></body></html>"
                data = data.encode()
            else:
                data = None
        if not data:
            not_found = b"<html><body><h1>Not Found</h1></body></html>"
            print(f"[ERRO] [{address[0]}:{address[1]}] {request_type.decode()} request returned error 404")

            header = 'HTTP/1.1 404 Not Found\r\n'+'Content-Length: ' + str(len(list(not_found)))+'\r\n'+'Content-type: text/html\r\n'+'Connection: Closed\r\n\r\n'
            data = not_found
        else:
            content_type = "text/html"
            if not direc:
                ext = file_path.split(".")[-1]   
                if ext == "txt" or ext == "htm" or ext == "html":
                    content_type = "text/html"
                elif ext== "css":
                    content_type = "text/css"
                elif ext=="png":
                    content_type = "image/png"
                elif ext=="jpeg" or ext=="jpg":
                    content_type = "image/jpeg"
                elif ext=="gif":
                    content_type = "image/gif"
                else:
                    content_type = "not implemented"


            if content_type == "not implemented":
                header = 'HTTP/1.1 501 Not Implemented\r\n'+'Connection: Closed\r\n\r\n'
                data = None
            else:
                header = 'HTTP/1.1 200 OK\r\n'+'Content-Length: ' + str(len(list(data)))+'\r\n'+'Content-type: ' + content_type + '\r\n'+'Connection: Closed\r\n\r\n'
            
    else:
        print(f"[ERRO] [{address[0]}:{address[1]}] {request_type.decode()} request returned error 501")
        header = 'HTTP/1.1 501 Not Implemented\r\n'+'Connection: Closed\r\n\r\n'


    if request_type == b'HEAD':
        data = None
        
    return [header, data]

if __name__ == "__main__":
    port = int(sys.argv[1])
    file_path = sys.argv[2]

    FR = FileReader()
    sel = selectors.DefaultSelector()


    J = Jewel(port, file_path, FR)
