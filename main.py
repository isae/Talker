import io
import os
import re
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler

import librosa
import numpy as np
import simpleaudio as sa
import soundfile as sf
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
        rs = bytes("OK", "utf-8")  # create response
        self.send_response(200)  # create header
        self.send_header("Content-Length", str(len(rs)))
        self.end_headers()
        self.wfile.write(rs)
        process_text(post_data)
        return


def add_chorus(data): # does not work
    copy = np.copy(data)
    delay_length = 5000
    copy_shifted = 0.1*np.concatenate((np.zeros(delay_length), copy[delay_length:]))
    return data+copy_shifted


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
    y, sr = sf.read(file)
    y_slow = librosa.effects.time_stretch(y, 0.4)
    y_pitch_shifted = librosa.effects.pitch_shift(y_slow, sr, n_steps=-10)
    y_chorus = add_chorus(y_pitch_shifted)
    file_name = str(uuid.uuid4()) + ".wav"
    sf.write(file_name, y_chorus, sr, subtype='PCM_24')
    wave_obj = sa.WaveObject.from_wave_file(file_name)
    wave_obj.play().wait_done()
    os.remove(file_name)


# sa.play_buffer(y, wave.num_channels, wave.bytes_per_sample, sr).wait_done()


# GOOGLE_APPLICATION_CREDENTIALS - path to JSON file must be set up
if __name__ == '__main__':
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, MyHandler)
    httpd.serve_forever()
