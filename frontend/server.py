from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


BACKEND_URL = "http://backend-service:8000"


class EventManagerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlsplit(self.path)
        if parsed_path.path == "/api/events/":
            self.proxy_events(parsed_path.query)
        elif parsed_path.path.startswith("/api/"):
            self.send_error(404, "API route not found")
        else:
            super().do_GET()

    def do_POST(self):
        parsed_path = urlsplit(self.path)
        if parsed_path.path != "/api/events/":
            self.send_error(404, "API route not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return

        if content_length < 0:
            self.send_error(400, "Invalid Content-Length")
            return

        body = self.rfile.read(content_length)
        self.proxy_events(parsed_path.query, method="POST", body=body)

    def proxy_events(self, query, method="GET", body=None):
        path = "/events/"
        if query:
            path = f"{path}?{query}"

        request = Request(
            f"{BACKEND_URL}{path}",
            data=body,
            headers={
                "Content-Type": self.headers.get(
                    "Content-Type", "application/json"
                )
            },
            method=method,
        )

        try:
            with urlopen(request, timeout=10) as response:
                self.send_backend_response(
                    response.status,
                    response.headers.get("Content-Type", "application/json"),
                    response.read(),
                )
        except HTTPError as error:
            self.send_backend_response(
                error.code,
                error.headers.get("Content-Type", "application/json"),
                error.read(),
            )
        except (URLError, TimeoutError):
            self.send_error(502, "Backend service is unavailable")

    def send_backend_response(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), EventManagerHandler).serve_forever()
