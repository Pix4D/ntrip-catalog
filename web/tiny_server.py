import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import argv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
try:
    from scripts import query as ntrip_query
except Exception as e:
    raise e


def ntrip_response(url):
    sourcetable_list = ntrip_query.get_streams_from_server(url)
    sourcetable = "\r\n".join(sourcetable_list)
    res = {
        "url": url,
        "source": "local-ntrip-catalog.json",
        "release": 0,
        "content": sourcetable,
    }
    return res


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "OPTIONS, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        logging.debug(
            "POST request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers)
        )
        logging.info(" POST request body: %s", post_data.decode("utf-8"))

        p = json.loads(post_data)
        res = ntrip_response(p["url"])
        message = json.dumps(res)
        msg_bytes = bytes(message, "utf8")
        logging.info(" POST response length: %d", len(msg_bytes))

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(msg_bytes)))
        self.end_headers()
        self.wfile.write(msg_bytes)


def run(port=8010):
    with HTTPServer(("", port), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
