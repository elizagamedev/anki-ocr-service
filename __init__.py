import http.client
import http.server
import json
import re
import sys
import threading
import time
import urllib.parse
from re import Pattern
from typing import Any, Optional, TextIO, Tuple

from aqt import mw as mw_optional
from aqt.main import AnkiQt
from aqt.qt import QApplication  # type: ignore

VERSION = "0.1.0"


def assert_is_not_none(optional: Optional[Any]) -> Any:
    if optional is None:
        raise Exception("Unexpected None")
    return optional


mw: AnkiQt = assert_is_not_none(mw_optional)


def log(message: Any, file: TextIO = sys.stdout):
    print(f"vgtranslate: {message}", file=file)


class Config:
    google_vision_api_key: str
    google_vision_confidence: float
    local_server_host: str
    local_server_port: int
    ocr_method: str
    text_replacements: list[Tuple[Pattern, str]]
    ztranslate_api_key: str

    def __init__(self, config: dict[str, Any]):
        self.google_vision_api_key = config.get("google_vision_api_key") or ""
        self.google_vision_confidence = config.get("google_vision_confidence") or 0.6
        self.local_server_host = config.get("local_server_host") or "localhost"
        self.local_server_port = config.get("local_server_port") or 4404
        self.ocr_method = config.get("ocr_method") or "ztranslate"

        text_replacements = config.get("text_replacements") or []
        self.text_replacements = [(re.compile(f), t) for (f, t) in text_replacements]

        self.ztranslate_api_key = config.get("ztranslate_api_key") or ""

    def replace_text(self, text: str) -> str:
        for f, t in self.text_replacements:
            text = f.sub(t, text)
        return text


config = Config(assert_is_not_none(mw.addonManager.getConfig(__name__)))


def call_ztranslate_service(
    image_data,
    lang,
    mode="fast",
    extra=None,
    body_kwargs=None,
):
    url = f"/service?output=text&target_lang={lang}&source_lang={lang}&mode={mode}"
    url += "&api_key=" + config.ztranslate_api_key
    if extra:
        for key in extra:
            url += "&" + key + "=" + extra[key]
    body = {"image": image_data}
    if body_kwargs:
        for key in body_kwargs:
            body[key] = body_kwargs[key]
    conn = http.client.HTTPSConnection("ztranslate.net", 443)
    conn.request("POST", url, json.dumps(body))
    rep = conn.getresponse()
    d = rep.read()
    output = json.loads(d)

    return output


def fix_neg_width_height(bb):
    if bb["w"] < 0:
        new_x = bb["x"] + bb["w"]
        new_w = -1 * bb["w"]
        bb["x"] = new_x
        bb["w"] = new_w
    if bb["h"] < 0:
        new_y = bb["y"] + bb["h"]
        new_h = -1 * bb["h"]
        bb["y"] = new_y
        bb["h"] = new_h
    return bb


def write_to_clipboard(text: str) -> None:
    QApplication.clipboard().setText(text)


class APIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Write to stdout instead of stderr.
        log(format % args)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title></title></head></html>", "utf-8"))
        self.wfile.write(bytes("<body>yo!</body></html>", "utf-8"))

    def do_POST(self):
        try:
            query = urllib.parse.urlparse(self.path).query
            if query.strip():
                query_components = dict(qc.split("=") for qc in query.split("&"))
            else:
                query_components = {}
            content_length = int(self.headers.get("content-length", 0))
            data = self.rfile.read(content_length)
            log(data[:80])
            data = json.loads(data)

            start_time = time.time()

            result = self._process_request(data, query_components)
            log(f"Request took {time.time() - start_time} seconds")
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            output = json.dumps(result)
            log(output[:80])
            self.send_header("Content-Length", len(output))
            self.end_headers()

            text = result.get("text")
            if text is not None:
                write_to_clipboard(config.replace_text(text))

            self.wfile.write(bytes(output, "utf-8"))
        except Exception as e:
            log(e)

    def _process_request(self, body, query):
        lang = query.get("source_lang")
        mode = query.get("mode", "fast")

        error_string = ""

        image_data = body.get("image")

        if config.ocr_method == "ztranslate":
            # pass the call onto the ztranslate service api...

            body_kwargs = {k: v for k, v in body.items() if k != "image"}

            output = call_ztranslate_service(
                image_data=image_data,
                lang=lang,
                mode=mode,
                body_kwargs=body_kwargs,
            )
            return output
        elif config.ocr_method == "google_vision":
            log("using google......")
            confidence = config.google_vision_confidence

            data, raw_output = self.google_ocr(image_data, lang)
            if not data:
                error_string = "No text found."

            data = self.process_output(
                data, raw_output, image_data, lang, confidence=confidence
            )

            output_data = {}

            # TODO: add text to output_data

            if error_string:
                output_data["error"] = error_string
            return output_data

    def google_ocr(self, image_data, source_lang):
        doc = {
            "requests": [
                {
                    "image": {"content": image_data},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                }
            ]
        }

        # load_image(img_data).show()
        if source_lang:
            doc["requests"][0]["imageContext"] = {"languageHints": [source_lang]}

        body = json.dumps(doc)

        uri = "/v1p1beta1/images:annotate?key="
        uri += config.google_vision_api_key

        data = self._send_request("vision.googleapis.com", 443, uri, "POST", body)
        output = json.loads(data)
        log("google output")
        log(output)
        if output.get("responses", [{}])[0].get("fullTextAnnotation"):
            return output["responses"][0]["fullTextAnnotation"], output
        else:
            return {}, {}

    def process_output(
        self, data, raw_data, image_data, source_lang=None, confidence=0.6
    ):
        text_colors = list()
        for entry in raw_data.get("responses", []):
            for page in entry["fullTextAnnotation"]["pages"]:
                for block in page["blocks"]:
                    text_colors.append(["ffffff"])

        results = {"blocks": [], "deleted_blocks": []}
        for page in data.get("pages", []):
            for num, block in enumerate(page.get("blocks", [])):
                this_block = {
                    "source_text": [],
                    "language": "",
                    "translation": "",
                    "bounding_box": {"x": 0, "y": 0, "w": 0, "h": 0},
                    "confidence": block.get("confidence"),
                    "text_colors": text_colors[num],
                }

                if block.get("confidence", 0) < confidence:  # and False:
                    continue
                bb = block.get("boundingBox", {}).get("vertices", [])
                this_block["bounding_box"]["x"] = bb[0].get("x", 0)
                this_block["bounding_box"]["y"] = bb[0].get("y", 0)
                this_block["bounding_box"]["w"] = bb[2].get("x", 0) - bb[0].get("x", 0)
                this_block["bounding_box"]["h"] = bb[2].get("y", 0) - bb[0].get("y", 0)
                fix_neg_width_height(this_block["bounding_box"])

                for paragraph in block.get("paragraphs", []):
                    for word in paragraph.get("words", []):
                        for symbol in word.get("symbols", []):
                            if (
                                symbol["text"] == "."
                                and this_block["source_text"]
                                and this_block["source_text"][-1] == " "
                            ):
                                this_block["source_text"][-1] = "."
                            else:
                                this_block["source_text"].append(symbol["text"])
                        this_block["source_text"].append(" ")
                    this_block["source_text"].append("\n")
                this_block["source_text"] = (
                    "".join(this_block["source_text"]).replace("\n", " ").strip()
                )
                this_block["original_source_text"] = this_block["source_text"]
                results["blocks"].append(this_block)
        return results

    def _send_request(self, host, port, uri, method, body=None):
        conn = http.client.HTTPSConnection(host, port)
        if body is not None:
            conn.request(method, uri, body)
        else:
            conn.request(method, uri)
        response = conn.getresponse()
        return response.read()


def main():
    host = config.local_server_host
    port = config.local_server_port
    log(f"starting server: host={host}, port={port}")
    httpd = http.server.ThreadingHTTPServer((host, port), APIHandler)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()


main()
