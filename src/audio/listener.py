import collections
import webrtcvad
import pyaudio

VAD_MODE = 2  # 0-3: 0 is most aggressive, 3 is least
CHUNK_DURATION_MS = 30
SAMPLE_RATE = 16000
FRAME_DURATION_MS = CHUNK_DURATION_MS
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
NUM_PADDING_CHUNKS = 10
NUM_WINDOW_CHUNKS = 10

FORMAT = pyaudio.paInt16
CHANNELS = 1

def listen_with_vad():
    vad = webrtcvad.Vad(VAD_MODE)
    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK_SIZE)

    print("Listening for speech...")
    ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
    triggered = False
    voiced_frames = []

    try:
        while True:
            chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            is_speech = vad.is_speech(chunk, SAMPLE_RATE)

            if not triggered:
                ring_buffer.append((chunk, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > 0.9 * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        voiced_frames.append(f)
                    ring_buffer.clear()
            else:
                voiced_frames.append(chunk)
                ring_buffer.append((chunk, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > 0.9 * ring_buffer.maxlen:
                    break
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

    return b''.join(voiced_frames)
