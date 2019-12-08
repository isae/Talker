import io
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

import simpleaudio as sa
from google.cloud import texttospeech

LANG_RU = 'ru-RU'
LANG_EN = 'en-US'
rus_character = re.compile(r'[А-Яа-я]')
client = texttospeech.TextToSpeechClient()


class MyHandler(BaseHTTPRequestHandler):

    def __init__(self, req, client_addr, server):
        BaseHTTPRequestHandler.__init__(self, req, client_addr, server)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")
        response(self, "OK")
        process_text(post_data)
        return 200


def response(self, message):
    response = bytes(message, "utf-8")  # create response

    self.send_response(200)  # create header
    self.send_header("Content-Length", str(len(response)))
    self.end_headers()

    self.wfile.write(response)


def process_text(text):
    if re.search(rus_character, text):
        lang_code = LANG_RU
    else:
        lang_code = LANG_EN
    response = client.synthesize_speech(
        texttospeech.types.SynthesisInput(text=text),
        texttospeech.types.VoiceSelectionParams(
            language_code=lang_code,
            ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE
        ),
        texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)
    )
    file = io.BytesIO(response.audio_content)
    wave_obj = sa.WaveObject.from_wave_file(file)
    play_obj = wave_obj.play()
    play_obj.wait_done()


# GOOGLE_APPLICATION_CREDENTIALS - path to JSON file must be set up
if __name__ == '__main__':
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, MyHandler)
    httpd.serve_forever()
