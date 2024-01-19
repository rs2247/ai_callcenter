""" Uses the real-time endpoint to calculate total latency.
    Python version: 3.6+
    Dependencies (use `pip install X` to install a dependency):
      - websockets
    Usage:
      python latency.py -k 'YOUR_DEEPGRAM_API_KEY' /path/to/audio.wav
    Limitations:
      - Only parses signed, 16-bit little-endian encoded WAV files.
    Notes:
      - Need a file? Grab one here: http://static.deepgram.com/examples/interview_speech-analytics.wav
"""

""" To run, type
    $ python3 playground/andre/latency_test.py -k 'YOUR_DEEPGRAM_API_KEY' playground/andre/recorded_audio_benchmark.wav

"""

import argparse
import asyncio
import base64
import json
import sys
import wave
import websockets

# Mimic sending a real-time stream by sending this many seconds of audio at a time.
REALTIME_RESOLUTION = 0.020

async def run(data, key, channels, sample_width, sample_rate):
    """ Connect to the Deepgram real-time streaming endpoint, stream the data
        in real-time, and print out the responses from the server.

        This uses a pre-recorded file as an example. It mimics a real-time
        connection by sending `REALTIME_RESOLUTION` seconds of audio every
        `REALTIME_RESOLUTION` seconds of wall-clock time.

        This is a toy example, since it uses a pre-recorded file. In a real use
        case, you'd be streaming the audio stream itself. If you actually have
        pre-recorded audio, use Deepgram's pre-recorded mode instead.
    """
    # How many bytes are contained in one second of audio.
    byte_rate = sample_width * sample_rate * channels

    audio_cursor = 0.

    # Connect to the real-time streaming endpoint, attaching our API key.
    async with websockets.connect(
        f'wss://api.deepgram.com/v1/listen?model=nova-2&language=pt-BR&channels={channels}&sample_rate={sample_rate}&encoding=linear16',
        extra_headers={
            'Authorization': 'Token {}'.format(key)
        }
    ) as ws:
        async def sender(ws):
            """ Sends the data, mimicking a real-time connection.
            """
            nonlocal data, audio_cursor
            try:
                total = len(data)
                while len(data):
                    # How many bytes are in `REALTIME_RESOLUTION` seconds of audio?
                    i = int(byte_rate * REALTIME_RESOLUTION)
                    chunk, data = data[:i], data[i:]
                    # Send the data
                    await ws.send(chunk)
                    # Move the audio cursor
                    audio_cursor += REALTIME_RESOLUTION
                    # Mimic real-time by waiting `REALTIME_RESOLUTION` seconds
                    # before the next packet.
                    await asyncio.sleep(REALTIME_RESOLUTION)

                # A CloseStream message tells Deepgram that no more audio
                # will be sent. Deepgram will close the connection once all
                # audio has finished processing.
                await ws.send(json.dumps({
                    "type": "CloseStream"
                }))
            except Exception as e:
                print(f'Error while sending: {e}')
                raise

        async def receiver(ws):
            """ Print out the messages received from the server.
            """
            nonlocal audio_cursor
            transcript_cursor = 0.
            min_latency = 0
            max_latency = 0
            avg_latency_num = 0
            avg_latency_den = 0
            async for msg in ws:
                msg = json.loads(msg)
                # print(msg)
                if 'request_id' in msg:
                    # This is the final metadata message. It gets sent as the
                    # very last message by Deepgram during a clean shutdown.
                    # There is no transcript in it.
                    continue
                # if msg['is_final']:
                #     continue
                # Just a moment ago -- right before we received this message --
                # is when the latency was at its worse. So measure max latency
                # and then update the transcript_cursor
                cur_max_latency = audio_cursor - transcript_cursor

                transcript_cursor = msg['start'] + msg['duration']

                # Since we just received a message, latency is currently at its
                # best.
                cur_min_latency = audio_cursor - transcript_cursor

                # The average latency (as would be measured by a constant probe
                # or by a sampling profiler) is mathematically equivalent to a
                # weighted sum.
                avg_latency_num += (cur_min_latency + cur_max_latency) / 2 * msg['duration']
                avg_latency_den += msg['duration']

                # Update global max/min latencies.
                max_latency = max(max_latency or 0, cur_max_latency)
                min_latency = min(min_latency or 10**6, cur_min_latency)

                print(f'Measuring... Audio cursor = {audio_cursor:.3f}, Transcript cursor = {transcript_cursor:.3f}')
                print(f"Instant Average Latency: {(cur_min_latency + cur_max_latency) / 2} / Duration: {msg['duration']}")
                print()

            print(f'Min latency: {min_latency:.3f}')
            print(f'Avg latency: {avg_latency_num / (avg_latency_den or 1):.3f}')
            print(f'Max latency: {max_latency:.3f}')

        await asyncio.wait([
            asyncio.ensure_future(sender(ws)),
            asyncio.ensure_future(receiver(ws))
        ])

###############################################################################
def parse_args():
    """ Parses the command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Submits data to the real-time streaming endpoint.')
    parser.add_argument('-k', '--key', required=True, help='YOUR_DEEPGRAM_API_KEY (authorization)')
    parser.add_argument('input', help='Input file.')
    return parser.parse_args()

###############################################################################
def main():
    """ Entrypoint for the example."
    """
    # Parse the command-line arguments.
    args = parse_args()

    # Open the audio file.
    with wave.open(args.input, 'rb') as fh:
        (channels, sample_width, sample_rate, num_samples, _, _) = fh.getparams()
        assert sample_width == 2, 'WAV data must be 16-bit.'
        data = fh.readframes(num_samples)
    print(f'Channels = {channels}, Sample Rate = {sample_rate} Hz, Sample width = {sample_width} bytes, Size = {len(data)} bytes', file=sys.stderr)

    # Run the example.
    asyncio.get_event_loop().run_until_complete(run(data, args.key, channels, sample_width, sample_rate))

###############################################################################
if __name__ == '__main__':
    sys.exit(main() or 0)
