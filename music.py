import os           # access to file methods & environment variables
import subprocess   # running executable files
import serial       # communication with the Arduino
import serial.tools.list_ports # finding serial coms
import time         # note and process timing
import yaml         # config file
import re           # handles regex for yt links and more
import numpy as np  # math and matrices
import asyncio      # required for twitch bot
import pygame.midi  # testing note sequence
import yt_dlp as youtube_dl # download yt audio
from twitchio.ext import commands   # access to callback commands
from twitchio import Message        # access to chat messages & processing thereof
import logging  # only display error msgs (mainly cause of annoying warning msgs)
import warnings # ignore warnings from tensorflow
logging.getLogger().setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module='tensorflow')
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Suppress TensorFlow INFO and WARNING messages
from basic_pitch.inference import predict_and_save, ICASSP_2022_MODEL_PATH # model to predict MIDI for audio

# Twitch bot class to listen for messages
class TwitchBot(commands.Bot):

    def __init__(self):
        super().__init__(token='<fill in your twitch bot access token>', prefix='!', initial_channels=['uorover'])

    async def event_ready(self):
        print(f'Logged in as {self.nick}')

    # Message callback function
    async def event_message(self, message: Message):

        # Grab globals to control playback of music
        global stop, toggle
        
        # Handle custom commands
        if message.content == "stop":
            if not stop:
                stop = True
                print("Halted playing!")
            else:
                print("Cannot stop music since nothing is playing!")
        elif message.content == "toggle":
            if not stop:
                toggle = not toggle
                print("Toggled playing!")
            else:
                print("Cannot toggle music since nothing is playing!")
        elif message.content == "replay":
            stop = True
            note_sequence = await midi_to_notes("audio_basic_pitch")
            await write_to_serial(note_sequence)
        
        elif (message.content.split(" ")[0] == "custom"):
            try:
                stop = True
                midi_file = message.content.split(" ")[1]
                note_sequence = await midi_to_notes(midi_file)
                await write_to_serial(note_sequence)
            except Exception as e:
                print(f"File error while attempting to convert mid file: {e}")

        elif (message.content.split(" ")[0] == "test"):
            try:
                stop = True
                midi_file = message.content.split(" ")[1]
                note_sequence = await midi_to_notes(midi_file)
                await test_song(note_sequence)
            except Exception as e:
                print(f"File error while attempting to convert mid file: {e}")
        
        # Look for a YouTube link in the message
        youtube_link = extract_youtube_link(message.content)
        if youtube_link:
            stop = True
            print(f"Received YouTube link: {youtube_link}")
            # Run the YouTube processing in the background
            asyncio.create_task(process_youtube_link(youtube_link))

# Write data to serial port asynchronously
async def write_to_serial(note_sequence):

    global stop, toggle
    
    command = "steppers_reboot;!" # Reboot stepper drivers since they can sometimes stop moving the steppers 
    ser.write(command.encode())
    await asyncio.sleep(0.25)     # Wait for them to reboot

    # Timer start when link has been received (until music starts playing on the arm)
    start_time = time.time()
    
    stop = False
    toggle = True

    i = 0
    while i < len(note_sequence) and not stop:
        if toggle:
            command = "X;"
            if note_sequence[i] == 240:  # End of score
                i += 1
            elif note_sequence[i] >= 144:  # Note on events
                hz = int(440 * (2 ** ((float(note_sequence[i+1]) - 69) / 12)))
                channel = note_sequence[i] - 144
                command += f"{channel};{hz};!"
                ser.write(command.encode())
                i += 2
                if verbose == "True":
                    print(f"Channel {channel} playing {hz}Hz, ",end=' ')
            elif note_sequence[i] >= 128:  # Note off events
                channel = note_sequence[i] - 128
                command += f"{channel};0;!"
                ser.write(command.encode())
                i += 1
                if verbose == "True":
                    print(f"Channel {channel} off, ",end=' ')
            else:  # Holding time for notes
                hold_time = float((note_sequence[i] << 8) + note_sequence[i + 1]) / 1000.0
                if verbose == "True":
                    print("\nHold ", hold_time / tempo, "s")
                await asyncio.sleep(hold_time / tempo)
                i += 2
        elif not toggle:
            await asyncio.sleep(0.1)

    command = "X;0;0;!X;1;0;!X;2;0;!" # stop motors when not playing
    ser.write(command.encode())

    elapsed_time = time.time() - start_time
    print(f"\nSong played for: {elapsed_time:.2f} seconds")

    stop = False
    toggle = True

# Mimics write_to_serial by playing the tune using pygame
async def test_song(note_sequence):

    global stop, toggle

    # Timer start when link has been received (until music starts playing on the arm)
    start_time = time.time()
    
    stop = False
    toggle = True
    pygame.midi.init()
    player = pygame.midi.Output(0)
    player.set_instrument(0)

    i = hz = 0
    while i < len(note_sequence) and not stop:
        if toggle:
            if note_sequence[i] == 240:  # End of score
                i += 1
            elif note_sequence[i] >= 144:  # Note on events
                hz = note_sequence[i+1]
                channel = note_sequence[i] - 144
                player.note_on(hz, 127)
                i += 2
                if verbose == "True":
                    print(f"Channel {channel} playing {hz}Hz, ",end=' ')
            elif note_sequence[i] >= 128:  # Note off events
                channel = note_sequence[i] - 128
                player.note_off(hz, 127)
                i += 1
                if verbose == "True":
                    print(f"Channel {channel} off, ",end=' ')
            else:  # Holding time for notes
                hold_time = float((note_sequence[i] << 8) + note_sequence[i + 1]) / 1000.0
                if verbose == "True":
                    print("\nHold ", hold_time / tempo, "s")
                await asyncio.sleep(hold_time / tempo)
                i += 2
        elif not toggle:
            await asyncio.sleep(0.1)

    elapsed_time = time.time() - start_time
    print(f"\nSong played for: {elapsed_time:.2f} seconds")

    del player
    pygame.midi.quit()  

    stop = False
    toggle = True
    
# Combine all steps into a single async task
async def process_youtube_link(youtube_link):

    # Timer start when link has been received (until music starts playing on the arm)
    start_time = time.time()

    await download_youtube_audio(youtube_link)
    await mp3_to_midi()
    note_sequence = await midi_to_notes("audio_basic_pitch")
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    print(f"\nTime from downloading to playing audio: {elapsed_time:.2f} seconds")

    await write_to_serial(note_sequence)
    
# MIDI to note sequence
async def midi_to_notes(midi_file):

    await run_miditones(midi_file)
    
    c_file = midi_file+".c"
    with open(c_file, "r") as file:
        data = file.read()

    start = data.find('{') + 1
    end = data.find('}')
    data = data[start:end].strip()

    cleaned_data = data.replace("// Track 0", "").replace(" ", "").replace("\n", "")

    data_list = cleaned_data.split(',')

    processed_data = [int(item.strip(), 16) if item.strip().startswith('0x') else int(item.strip()) for item in data_list]

    return np.array(processed_data, dtype=int)

# Function to load config.yaml parameters
def load_config():
    
    global verbose, tempo, baudrate, serial_port, channel_name, oauth_token

    # Load the YAML file
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        print(f"Loaded config: {config}")

    # Check if config is None
    if config is not None:
        verbose = config.get('verbose', "False")
        tempo = config.get('tempo', 1.0)
        baudrate = config.get('baudrate', 115200)
        serial_port = config.get('serial_port', "COM5")
        channel_name = config.get('channel_name', "")
        oauth_token = config.get('oauth_token', "")
    else:
        print("Warning: config.yaml is empty or not formatted correctly.")

# Download YouTube audio as MP3
async def download_youtube_audio(youtube_link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'playlist_items': '1',  # Only download the first video from a playlist
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_link])

# Convert MP3 to MIDI
async def mp3_to_midi():
    midi_file = "audio_basic_pitch.mid"
    if os.path.exists(midi_file):
        os.remove(midi_file)
    try:
        predict_and_save(
            ["audio.mp3"],
            output_directory='.',
            save_midi=True,
            sonify_midi=False,
            save_model_outputs=False,
            save_notes=False,
            model_or_model_path=ICASSP_2022_MODEL_PATH
        )
    except Exception as e:
        print(f"Error in mp3_to_midi: {e}")
    return midi_file

# Run miditones on the midi file to obtain a .c file containing an array of note on/off events and timings
async def run_miditones(mid_file):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    miditones_path = os.path.join(current_dir, "miditones", "miditones.exe")
    subprocess.run([miditones_path, "-t=3", "-c=7", mid_file])

# Uses RegEx to extract a YouTube link
def extract_youtube_link(text: str):

    # Regex to match a wider variety of YouTube links
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube\.com/watch\?v=|'
        'youtube\.com/embed/|'
        'youtube\.com/v/|'
        'youtu\.be/|'
        'm\.youtube\.com/watch\?v=)'
        '[\w-]+'
        r'(?:&\S*)?'
    )
    match = re.search(youtube_regex, text)
    return match.group(0) if match else None

# Extracts a specific message from chat to play custom mid files; i.e.: "custom file.mid"
async def extract_custom_mid(filename):
    pattern = r'^custom\s+(\S+\.mid)$'
    match = re.match(pattern, filename)
    if match:
        return [match.group(1)]
    return []

# If @serial_port from the config file is empty, iterate and attempt connection with the first valid arduino sketch via a response request
def find_arduino():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        try:
            ser = serial.Serial("COM7", baudrate, timeout=1)
            time.sleep(1.0) # delay required for device to initialize and run setup
            ser.write("ARDUINO?;!".encode())
            time.sleep(0.1) # allow ample time for message to send
            
            response = None
            if ser.in_waiting:
                response = ser.read_until(b'!')[:-1].decode('utf-8')

            if response == "ARM":
                print(f"Arduino found and connected on {port.device}.")
                return ser
            else:
                ser.close()
        except serial.SerialException as e:
            print(f"Error opening serial connection on {port.device}: {e}")
    return None

# Runs bot in the async loop (required as Twitchio guide)
async def main():
    bot = TwitchBot()
    await bot.start()

# Main entry point
if __name__ == "__main__":

    # Variables for music playback
    stop = False
    toggle = True

    # Configuration parameters
    verbose = tempo = baudrate = serial_port = channel_name = oauth_token = None
    load_config()

    ser = None
    if (serial_port == ""):
        ser = find_arduino()
        if ser is None:
            print("Could not establish a serial connection on any port.")
    else:
        # Try establishing an arduino connection on the speficied port
        try:
            ser = serial.Serial(serial_port, baudrate, timeout=1)
            print("Serial connection opened successfully.")
        except serial.SerialException as e:
            print(f"Error opening serial connection on port {serial_port}: {e}")

    # Run the bot
    asyncio.run(main())
