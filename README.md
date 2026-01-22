
# Robotic Arm Player (RAP)

<a href="https://www.youtube.com/watch?v=fO1SlkeHADE" target="_blank">
  <img src="https://img.youtube.com/vi/fO1SlkeHADE/maxresdefault.jpg" alt="Watch the video">
</a> 

<div align="center">
   <a href="https://www.youtube.com/watch?v=fO1SlkeHADE" target="_blank">Watch the Video!
</a> 
  
</div>

## Overview

This one-week project is a Python & Arduino application designed to be run on the Windows OS. It downloads audio from YouTube links, converts them to MIDI files using Spotify's ACASSP 2022 model, converts the MIDI file into a sequence of commands sent to a serial port to control a few steppers on a robotic arm. Originally intended for fundraising; i.e.: Twitch viewer donates 1$ together with a link and the arm plays a fixed segment of it.

## Requirements

### Python Packages

This project requires several Python packages. You can install them using `pip`. Run the following command to install all the required packages:

```bash
pip install pyserial pydub numpy youtube-dlp tensorflow basic-pitch twitchio pygame
```

### External Tools

- **FFmpeg**: Required by `youtube-dlp` for audio extraction. Make sure FFmpeg is installed and added to your system's PATH. You can download it from [FFmpeg's official website](https://ffmpeg.org/download.html).

- **Miditones**: An external executable for MIDI processing already included in the project. Check it out: [miditones GitHub repository](https://github.com/LenShustek/miditones/tree/master).

## Environment Variables

The script requires certain environment variables to be set. You can configure them in the `config.yaml` file, which should be located in the same directory as the script. The following variables are used:

- `verbose`: A flag for verbosity (`"False"` or `"True"`).
- `tempo`: Tempo or playback for note duration (default is `1.0`).
- `baudrate`: Baud rate for serial communication (default is `115200`).
- `serial_port`: Serial port to which the Arduino is connected. Empty by default, the script will automatically connect to the correct port.
- `oauth_token`: OAuth token for Twitch authentication.

## Setup Instructions

1. **Install Python and pip**: [Download](https://www.python.org/downloads/) Python 3.7 or higher along with `pip`.

2. **Install Required Packages**: Use the command provided above to install the necessary Python packages.

3. **Install FFmpeg**: [Download](https://ffmpeg.org/download.html) and install FFmpeg. Add the FFmpeg bin directory to your system’s PATH.

4. **Obtain your OAuth Token from Twitch**: Go through the [guide](https://dev.twitch.tv/docs/api/get-started/).

5. **Configure `config.yaml`**: Create a `config.yaml` file in the project directory and configure it with the required parameters. Here is a sample configuration:

   ```yaml
   verbose: "True"
   tempo: 1.0
   baudrate: 115200
   serial_port: "COM5"
   channel_name: "your_twitch_channel_name"
   oauth_token: "your_oauth_token_here"
   ```
   
6. **Upload Arduino Code**: on the Arduino IDE, ensure that you have everything setup such as the `board` and `port` and upload the code provided. The arduino sketch can be found inside the `rap` folder.

7. **Run the Script**: Execute the script using Python:

   ```bash
   python music.py
   ```

## Usage

1. **Play any YouTube Audio**: In the Twitch chat, paste a YouTube link to request it be played. For example:

   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
   Or alternatively play a custom MIDI file by typing in the chat:
   ```
   custom still_alive
   ```
   Finally, if you want to test without a serial device/steppers, just run:
   ```
   test still_alive
   ```
   this will play the MIDI as it should on the steppers.


2. **Stop, Toggle or Replay**: In the Twitch chat, send `stop` to quit playing a song completely or alternatively `toggle` to pause or resume playing a tune or `replay` to play the last song.

## Troubleshooting

- **FFmpeg Not Found**: Ensure FFmpeg is installed and its executable is in your system’s PATH.
- **Miditones Not Found**: Verify that the `miditones` executable is in the correct directory.
- **Serial Port Errors**: Check that the correct serial port is specified/unoccupied and that your hardware is properly connected.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
