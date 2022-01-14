from posixpath import split
from tkinter import *
from tkinter import scrolledtext
import threading
from tkinter.filedialog import askopenfilename, asksaveasfilename
import wave
import pyaudio
import os
from asr import ASR_from_files, ASR_live
import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
SECONDS = 5
record_on = False
counter = 0

class GUI :
    def __init__(self):
        self.p = None
        self.stream = None
        self.frames = []
        self.filename = ""

        self.asr_from_files = ASR_from_files()
        # TODO: implement live mic decoding
        self.asr_live = ASR_live()

        self.window = Tk()
        self.window.title('ASR Real-Time Bahasa Indonesia')
        self.window.geometry('1000x500')
        self.window.configure(background = '#353535')
        self.window.columnconfigure(0, weight=3)
        self.window.columnconfigure(1, weight=2)

        self.label_transcription = Label(
            self.window,
            text="Transcription", font=("Helvetica 12 underline"),
            fg="White",
            bg='#353535'
        )
        self.label_transcription.grid(
            row=0, column=0,
            pady=20,
        )

        self.label_microphone = Label(
            self.window,
            text="Microphone", font=("Helvetica 12 underline"),
            fg="White",
            bg='#353535'
        )
        self.label_microphone.grid(
            row=0, column=1,
            columnspan=2
        )

        self.scrolledtext_transcription = scrolledtext.ScrolledText(
            self.window,
            width=60, height=20,
            font="Helvetica 10"
        )
        self.scrolledtext_transcription.grid(
            row=1, column=0,
        )

        self.button_record = Button(
            self.window,
            text="Record",
            command=self.voice_record
        )
        self.button_record.grid(
            row=1, column=1,
            sticky=N
        )

        self.button_stop = Button(
            self.window,
            text="Stop",
            command=self.stop_recording
        )
        self.button_stop.grid(
            row=1, column=1,
            pady=50,
            sticky=N
        )

        self.button_stop_and_decode = Button(
            self.window,
            text="Stop and decode",
            command=self.stop_and_decode
        )
        self.button_stop_and_decode.grid(
            row=1, column=1,
            pady=100,
            sticky=N
        )

        self.label_counter = Label(
            self.window,
            text="00:00", font=("Helvetica 10")
        )
        self.label_counter.grid(
            row=1, column=2,
            padx=60, pady=5,
            sticky=N
        )

        self.button_save = Button(
            self.window,
            text="Save",
            command=self.save_audio
        )
        self.button_save.grid(
            row=1, column=1,
            sticky=S
        )

        self.button_play = Button(
            self.window,
            text="Play",
            command=self.play_audio
        )
        self.button_play.grid(
            row=1, column=2,
            pady=50,
            sticky=N
        )

        self.label_filename = Label(
            self.window,
            text="No file selected",
        )
        self.label_filename.grid(
            row=1, column=2,
            padx=60, pady=50,
            sticky=S
        )

        self.button_load = Button(
            self.window,
            text="Load",
            command=self.load_audio
        )
        self.button_load.grid(
            row=1, column=2,
            padx=20,
            sticky=S
        )

        self.button_decode_from_file = Button(
            self.window,
            text="Decode from file",
            command=self.decode_from_file
        )
        self.button_decode_from_file.place(
            relx=0.05, rely=0.95,
            anchor="sw"
        )

        # TODO: implement live mic decoding
        self.button_live_decoding = Button(
            self.window,
            text="Live decoding",
            command=self.live_decoding
        )
        self.button_live_decoding.place(
            relx=0.5, rely=0.95,
            anchor="s"
        )

        self.button_exit = Button(
            self.window,
            text="Exit",
            width=10,
            command=self.exit_app
        )
        self.button_exit.place(
            relx=0.95, rely=0.95,
            anchor="se"
        )

    def start_counter(self, label):
        def count() :
            global counter
            if not record_on :
                return
            counter += 1
            m, s = counter % 3600 // 60, counter % 3600 % 60
            label.config(
                text="{:02d}:{:02d}".format(m, s), font="Helvetica 10 bold",
                fg="red"
            )
            label.after(1000, count)
        count()

    def start_recording(self) :
        global record_on, counter
        counter = 0
        self.start_counter(self.label_counter)
        self.stream.start_stream()
        while record_on :
            data = self.stream.read(CHUNK,)
            self.frames.append(data)
            print(counter)

    def voice_record(self) :
        global record_on
        if record_on :
            return
        self.frames.clear()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            rate=SAMPLE_RATE,
            channels=CHANNELS,
            format=FORMAT,
            frames_per_buffer=CHUNK,
            input=True
        )
        record_on = True
        t = threading.Thread(target=self.start_recording)
        t.start()
        print("Recording...")

    def stop_recording(self) :
        global record_on, counter
        if not record_on :
            return
        record_on = False
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.p.terminate()
        self.label_counter.config(
            font="Helvetica 10",
            fg="black"
        )
        print("Recording stopped...")

    def stop_and_decode(self) :
        global record_on, counter
        if not record_on :
            return
        record_on = False
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.p.terminate()
        self.label_counter.config(
            font="Helvetica 10",
            fg="black"
        )
        print("Recording stopped...")

        self.filename = "data/tmp.wav"
        if os.path.exists(self.filename) :
            os.remove(self.filename)

        wv = wave.open(self.filename, "wb")
        wv.setnchannels(CHANNELS)
        wv.setsampwidth(self.p.get_sample_size(FORMAT))
        wv.setframerate(SAMPLE_RATE)
        wv.writeframes(b''.join(self.frames))
        wv.close()

        self.label_counter.config(
            text="00:00"
        )
        self.label_filename.config(text=(os.path.relpath(self.filename, ".")))

        if not os.path.exists("tmp") :
            os.mkdir("tmp")

        tmp_scp_path = os.path.join("tmp", os.path.basename(self.filename).split('.')[0]) + ".scp"

        with open(tmp_scp_path, "w") as tmp_scp :
            tmp_scp.write(os.path.basename(self.filename).split('.')[0] + " " + os.path.relpath(self.filename) + "\n")

        start_time = time.time()
        decode_str = self.asr_from_files.decode(tmp_scp_path, scp_file=tmp_scp_path)
        decode_time = time.time() - start_time
        os.remove(tmp_scp_path)

        rtf = decode_time / len(self.frames)
        print(rtf)
        decode_str += "\nDecoded in {} seconds, over a total of {} frames.\nRTF = {} / {} = {}".format(decode_time, len(self.frames), decode_time, len(self.frames), rtf)

        self.scrolledtext_transcription.delete("1.0", END)
        self.scrolledtext_transcription.insert("1.0", decode_str)

    def save_audio(self) :
        global CHANNELS, FORMAT, SAMPLE_RATE, record_on
        if not self.frames :
            err_msg = "Record an audio first to save!"
            self.scrolledtext_transcription.delete("1.0", END)
            self.scrolledtext_transcription.insert("1.0", err_msg)
            return

        self.filename = asksaveasfilename(
            initialdir="./data",
            title="Save as",
            filetypes=[("Audio file", "*.wav"), ("All files", "*.*")],
            defaultextension=".wav"
        )

        wv = wave.open(self.filename, "wb")
        wv.setnchannels(CHANNELS)
        wv.setsampwidth(self.p.get_sample_size(FORMAT))
        wv.setframerate(SAMPLE_RATE)
        wv.writeframes(b''.join(self.frames))
        wv.close()
        self.frames.clear()
        self.label_counter.config(
            text="00:00"
        )
        self.label_filename.config(text=(os.path.relpath(self.filename, ".")))
        record_on = False

    def play(self, wave_file) :
        data = wave_file.readframes(CHUNK)
        while data :
            self.stream.write(data)
            data = wave_file.readframes(CHUNK)
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.p.terminate()

    def play_audio(self) :
        if self.filename == "" :
            err_msg = "Record or load an audio file to play!"
            self.scrolledtext_transcription.delete("1.0", END)
            self.scrolledtext_transcription.insert("1.0", err_msg)
            return

        wv = wave.open(self.filename, "rb")
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.p.get_format_from_width(wv.getsampwidth()),
            channels=CHANNELS,
            rate=wv.getframerate(),
            output=True
        )

        t = threading.Thread(target=self.play, args=(wv,))
        t.start()

    def load_audio(self) :
        self.filename = askopenfilename(
            initialdir="./data",
            title="Load audio file",
            filetypes=[("Audio file", "*.wav"), ("All files", "*.*")],
            defaultextension=".wav"
        )
        if self.filename != "" :
            self.label_filename.config(text=os.path.relpath(self.filename, "."))
        else :
            self.label_filename.config("No file selected")

    def decode_from_file(self) :
        if self.filename == "" :
            err_msg = "Record or load an audio file to decode!"
            self.scrolledtext_transcription.delete("1.0", END)
            self.scrolledtext_transcription.insert("1.0", err_msg)
            return
        if not os.path.exists("tmp") :
            os.mkdir("tmp")

        tmp_scp_path = os.path.join("tmp", os.path.basename(self.filename).split('.')[0]) + ".scp"
        with open(tmp_scp_path, "w") as tmp_scp :
            tmp_scp.write(os.path.basename(self.filename).split('.')[0] + " " + os.path.relpath(self.filename) + "\n")
        decode_str = self.asr_from_files.decode(tmp_scp_path, scp_file=tmp_scp_path)
        os.remove(tmp_scp_path)

        self.scrolledtext_transcription.delete("1.0", END)
        self.scrolledtext_transcription.insert("1.0", decode_str)

    # TODO: implement live mic decoding
    def live_decoding(self) :
        global record_on
        def start_rec() :
            global counter
            counter = 0
            prev_counter = 0
            buffer_frames = []
            self.start_counter(self.label_counter)
            self.stream.start_stream()
            while record_on :
                data = self.stream.read(CHUNK,)
                self.frames.append(data)
                buffer_frames.append(data)
                if prev_counter+1 == counter :
                    prev_counter = counter
                    print(prev_counter)
                    self.filename = "data/buf_tmp.wav"
                    if os.path.exists(self.filename) :
                        os.remove(self.filename)
                    wv = wave.open(self.filename, "wb")
                    wv.setnchannels(CHANNELS)
                    wv.setsampwidth(self.p.get_sample_size(FORMAT))
                    wv.setframerate(SAMPLE_RATE)
                    wv.writeframes(b''.join(buffer_frames))
                    wv.close()
                    if not os.path.exists("tmp") :
                        os.mkdir("tmp")
                    tmp_scp_path = os.path.join("tmp", os.path.basename(self.filename).split('.')[0]) + ".scp"
                    with open(tmp_scp_path, "w") as tmp_scp :
                        tmp_scp.write(os.path.basename(self.filename).split('.')[0] + " " + os.path.relpath(self.filename) + "\n")
                    decode_str = self.asr_from_files.decode(tmp_scp_path, scp_file=tmp_scp_path)
                    decode_str = " ".join(decode_str.split()[1:]) + " " if decode_str.split()[1:] else ""
                    os.remove(tmp_scp_path)
                    print("*" + decode_str + "*")
                    buffer_frames.clear()
                    self.scrolledtext_transcription.insert(END, decode_str)
        if not record_on :
            self.scrolledtext_transcription.delete("1.0", END)
            self.button_live_decoding.config(text="Stop decoding")
            self.frames.clear()
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                rate=SAMPLE_RATE,
                channels=CHANNELS,
                format=FORMAT,
                frames_per_buffer=CHUNK,
                input=TRUE
            )
            record_on = True
            t = threading.Thread(target=start_rec)
            t.start()
        else :
            self.button_live_decoding.config(text="Live decoding")
            self.filename = "data/tmp.wav"
            if os.path.exists(self.filename) :
                os.remove(self.filename)
            wv = wave.open(self.filename, "wb")
            wv.setnchannels(CHANNELS)
            wv.setsampwidth(self.p.get_sample_size(FORMAT))
            wv.setframerate(SAMPLE_RATE)
            wv.writeframes(b''.join(self.frames))
            wv.close()

            self.frames.clear()
            record_on = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.p.terminate()
            self.label_counter.config(
                font="Helvetica 10",
                fg="black"
            )

    def exit_app(self) :
        # self.p.terminate()
        self.window.quit()

# Main loop
if __name__ == "__main__" :
    gui = GUI()
    gui.window.mainloop()
