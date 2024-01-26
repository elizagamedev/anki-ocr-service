## `google_vision_api_key`
Private API key for [Google Cloud Vision](https://cloud.google.com/vision/docs).
Required if `ocr_method` is set to `"google_vision"`.

Default: `""`.

## `google_vision_confidence`
Minimum confidence at which to consider text returned by Google Cloud Vision to
be valid. Any text which falls below this threshold is discarded.

Default: `0.6`.

## `local_server_host`
Hostname for the local server. Set to `0.0.0.0` to accept incoming network
connections from other devices on your network.

Default: `localhost`.

## `local_server_port`
Port for the local server.

Default: `4404`.

## `ocr_method`
The method to use for OCR. Must be either `"ztranslate"` or `"google_vision"`.

Default: `"ztranslate"`.

## `text_replacements`
[Regular expression](https://docs.python.org/3/howto/regex.html) replacements to
perform on the detected text. A list of lists in the format `[["pattern1",
"replacement1"], ["pattern2", "replacement2"]]`. This can be useful for
stripping whitespace in Japanese text; for example, `[["\\s+", ""]]`.

Default: `[]`.

## `ztranslate_api_key`
Private API key for [ztranslate](https://www.ztranslate.net/). Required if
`ocr_method` is set to `"ztranslate"`.
