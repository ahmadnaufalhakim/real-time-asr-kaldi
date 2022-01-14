import wave
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()
print(p.get_device_count())
print(p.get_default_input_device_info())
print(p.get_default_output_device_info())

print()

for i in range(p.get_device_count()) :
    print(p.get_device_info_by_index(i))
    print("index", p.get_device_info_by_index(i)["index"])
    print("################")

stream = p.open(
    rate=RATE,
    channels=CHANNELS,
    format=FORMAT,
    frames_per_buffer=CHUNK,
    input=True)

frames = []

for i in range(int(RATE / CHUNK * RECORD_SECONDS)) :
    data = stream.read(CHUNK)
    frames.append(data)
    print(i)

print(" * done recording")

stream.stop_stream()
stream.close()
p.terminate()

# print(frames)

wv = wave.open(WAVE_OUTPUT_FILENAME, "wb")
wv.setnchannels(CHANNELS)
wv.setsampwidth(p.get_sample_size(FORMAT))
wv.setframerate(RATE)
wv.writeframes(b''.join(frames))
wv.close()

########################################

# from scipy.io.wavfile import write
# import sounddevice as sd
# print(sd.get_portaudio_version())
# print(sd.query_devices())

# SAMPLE_RATE = 44100
# SECONDS = 5

# MONO = 1
# STEREO = 2

# recording = sd.rec(int(SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=MONO)
# sd.wait()

# write("output.wav", SAMPLE_RATE, recording)