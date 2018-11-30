#!/usr/bin/env python
# Reflects the requests from HTTP methods GET, POST, PUT, and DELETE
# Written by Nathan Hamiel (2010)

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import argparse


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        request_path = self.path

        print("\n----- Request Start ----->\n")
        print(request_path)
        print(self.headers)
        print("<----- Request End -----\n")

        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        request_path = self.path

        print("\n----- Request Start ----->\n")
        print(request_path)

        request_headers = self.headers
        content_length = request_headers.getheaders('content-length')
        length = int(content_length[0]) if content_length else 0

        print(request_headers)
        print(self.rfile.read(length))
        print("<----- Request End -----\n")

        self.send_response(200)
        self.end_headers()

    do_PUT = do_POST
    do_DELETE = do_GET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4000)
    args = parser.parse_args()
    print('Listening on localhost:%s' % args.port)
    server = HTTPServer(('', args.port), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopped.')


if __name__ == "__main__":
    main()