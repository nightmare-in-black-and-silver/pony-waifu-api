from app.models.audio.buffered_speech_line import BufferedSpeechLine


class AudioBuffer:
    def __init__(self):
        self.lines: list[BufferedSpeechLine] = []