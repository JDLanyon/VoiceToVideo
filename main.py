import pyaudio
import cv2
import struct
import math
import pyvirtualcam
import configparser
import glob
import re

# SETUP

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
SHORT_NORMALIZE = (1.0/32768.0)

current_frame = 0
FMT = pyvirtualcam.PixelFormat.BGR
cam = pyvirtualcam.Camera(width=1280, height=720, fps=30, fmt=FMT)

images = []

config = configparser.ConfigParser()
config.read('config.conf')
use_exponential = config.getboolean('configuration', 'use_exponential')
folder = config['configuration']['folder']

# Avextro
# for i in range(16):
#     images.append(cv2.imread(f'Avextro/{i}.png'))

# Jackson
# for i in range(12):
#     images.append(cv2.imread(f'Jackson/{i}.png'))

# Donga
# for i in range(13):
#     images.append(cv2.imread(f'{folder}/{i}.png'))

# Count pngs and try to construct images list


# sort key (for sorting image files)

def numericalSort(value):
    numbers = re.compile(r'(\d+)')
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

# Set up part 2: electric boogaloo

try:
    # images = glob.glob(f'{folder}/*.png')
    images = sorted(glob.glob(f'{folder}/*.png'), key=numericalSort)

    # images.sort(key=lambda x: int(x.split('.')[0]))
    # images.sort()
    images = [cv2.imread(x) for x in images]

    if len(images) == 0:
        raise Exception('ERROR!\n Folder is empty.')
except Exception as e:
    print(e)
    input()
    exit()
except:
    print("ERROR!\n Could not construct list of images, please double check your folder name or dm Sausytime#6969 on discord.")
    input()
    exit()

WIDTH, HEIGHT = 1280, 720

res = []

for img in images:
    res.append(cv2.resize(img, dsize=(WIDTH,HEIGHT)))

# Get amplitude function

def get_rms(block):

    # RMS amplitude is defined as the square root of the
    # mean over time of the square of the amplitude.
    # so we need to convert this string of bytes into
    # a string of 16-bit samples...

    # we will get one short out for each
    # two chars in the string.
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    # iterate over the block.
    sum_squares = 0.0
    for sample in shorts:
    # sample is a signed short in +/- 32768.
    # normalize it to 1.0
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n

    return math.sqrt( sum_squares / count )

# display image according to amplitude

def displayImage(amplitude):
    global current_frame, cam

    # use exponential?
    indx = None
    if use_exponential:
        # ceil(-i (x-1)^2 +i)
        # this is basically an upside-down quadratic.
        indx = math.ceil(-len(images) * (amplitude - 1) ** 2 + len(images)) - 1
    else:
        indx = math.ceil(amplitude * len(images)) - 1

    if current_frame != indx:
        print(indx)
        current_frame = indx
        cam.send(res[indx])
        cam.sleep_until_next_frame()

def streamAudio():
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []
    try:
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
            amplitude = get_rms(data)
            displayImage(amplitude)
    except KeyboardInterrupt:
        pass

    # print("* done recording")
    #
    # stream.stop_stream()
    # stream.close()
    # p.terminate()
    #
    # wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    # wf.setnchannels(CHANNELS)
    # wf.setsampwidth(p.get_sample_size(FORMAT))
    # wf.setframerate(RATE)
    # wf.writeframes(b''.join(frames))
    # wf.close()
    #
    # rate, data = wavfile.read('output.wav')
    # t = np.arange(len(data[:,0]))*1.0/rate
    # pl.plot(t, data[:,0])
    # pl.show()

if __name__ == "__main__":
    streamAudio()
