import asyncio
import bleak
from bleak import BleakClient
import wave
from datetime import datetime
import numpy as np

# SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
# CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
AUDIO_FILE = "recorded_audio.wav"
SAMPLE_RATE = 16000  # Replace with the appropriate sample rate
SAMPLE_WIDTH = 2  # 16-bit audio
CHANNELS = 1  # Mono audio


async def main():
    print("Discovering AudioRecorder...")
    devices = await bleak.discover(timeout=5.0)
    audio_recorder = None
    for device in devices:
        print(device.name, device.address)
        if device.name == "Arduino":
            audio_recorder = device
            break

    if audio_recorder:

        def export_audio_data(audio_data):
            # Create a txt file of the data exported as numbers in a list
            # Name it base on current time in HH:MM:SS:MS format
            filename = datetime.now().strftime("%H-%M-%S-%f") + ".txt"

            long_audio_data = np.frombuffer(audio_data, dtype=np.int16)

            with open(filename, "w") as txt_file:
                txt_file.write(str(list(long_audio_data)))

        def process_audio_data(audio_data):
            # Create a WAV file and write the audio data
            # Name it base on current time in HH:MM:SS:MS format
            filename = datetime.now().strftime("%H-%M-%S-%f") + ".wav"

            long_audio_data = np.frombuffer(audio_data, dtype=np.int16)

            with wave.open(filename, "wb") as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(SAMPLE_WIDTH)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(long_audio_data)

        async with BleakClient(audio_recorder.address) as client:
            print("Connected to AudioRecorder")
            print("Discovering services...")
            services = await client.get_services()
            audio_service = services.get_service(SERVICE_UUID)
            audio_characteristic = audio_service.get_characteristic(CHARACTERISTIC_UUID)

            audio_data = bytearray()

            end_signal = b"\xFF"  # Example: Use 0xFF as the end signal value

            def handle_audio_data(sender, data):
                audio_data.extend(data)

                # Print the received data length
                print("Received", len(data), "bytes")

                print("Data:", data)

                # Check for the end signal value
                if data == [end_signal]:
                    print("End signal received after", len(audio_data), "bytes")
                    # Process the complete audio data
                    process_audio_data(audio_data)
                    export_audio_data(audio_data)
                    audio_data.clear()

            await client.start_notify(audio_characteristic.uuid, handle_audio_data)
            print("Recording audio...")

            # Wait for audio data or perform other tasks
            await asyncio.sleep(10)  # Example: Wait for 10 seconds

            await client.stop_notify(audio_characteristic.uuid)
            print("Recording stopped")

        process_audio_data(audio_data)
        export_audio_data(audio_data)
    else:
        print("AudioRecorder not found")


asyncio.run(main())