import pyaudio
import wave
import keyboard
import winsound
import soundfile as sf
import io
import numpy as np
import wave
import webrtcvad

class AudioManager:
    SILENCE_THRESHOLD = 30 # ms of silence to end recording

    def __init__(self, chunk=1024, sample_format=pyaudio.paInt16, channels=1, sample_rate=32000, max_silent_seconds = 1):
        self.recording = False
        self.frames = []
        self.chunk = chunk
        self.sample_format = sample_format
        self.channels = channels
        self.sample_rate = sample_rate
        self.p = None
        self.stream = None
        self.vad = webrtcvad.Vad(2)
        self.frames_per_treshold = int(sample_rate / 1000 * self.SILENCE_THRESHOLD)
        self.max_silent_seconds = max_silent_seconds

    # Starts live recording
    def start(self, voice_activity_detection= True):
        self.recording = True
        self.frames = []
        
        # detectable time subdivisions for which the VAD can detect silence
        time_subdivisions = int(self.max_silent_seconds * 1000 / self.SILENCE_THRESHOLD)
        silences = 0

        # Signal to notify the start of recording
        winsound.Beep(1000, 200)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.sample_format,
                                  channels=self.channels,
                                  rate=self.sample_rate,
                                  frames_per_buffer=self.chunk,
                                  input=True)

        while self.recording:
            detectable_frames = self.stream.read(self.frames_per_treshold)
            data = self.stream.read(self.chunk)
            self.frames.append(data)

            if voice_activity_detection:
                if not self.vad.is_speech(detectable_frames, self.sample_rate):
                    silences += 1

                    if silences >= time_subdivisions:
                        print('[Stream Stopped] Reached Silence Treshold')
                        self.stop()
                    

            if keyboard.is_pressed('q'):
                print('[Stream Stopped] Manual Termination')
                self.stop()

    # Stops live recording
    def stop(self):
        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    # Saves the recording to a .wav file
    def save(self, filename):
        if filename:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()

    def save_temp(self):
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()

        return buffer

        
        
                
    # Plays the audio file at the given file path
    def play_audio(self, audio_file_path):
        if audio_file_path:
            # Calculate the time elapsed since the start of the script
            # elapsed_time = time.time() - start_time
            # print(f"Time taken to start playing audio clip: {elapsed_time} seconds")
            
            with sf.SoundFile(audio_file_path, 'r') as sound_file:
                audio = pyaudio.PyAudio()
                stream = audio.open(format=pyaudio.paInt16, channels=sound_file.channels, rate=sound_file.samplerate, output=True)
                data = sound_file.read(self.chunk, dtype='int16')
                
                while len(data) > 0:
                    stream.write(data.tobytes())
                    data = sound_file.read(self.chunk, dtype='int16')

                stream.stop_stream()
                stream.close()
                audio.terminate()

    