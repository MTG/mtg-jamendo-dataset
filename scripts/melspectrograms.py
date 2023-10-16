from argparse import ArgumentParser

from essentia.standard import *
import essentia
import numpy


def load_audio(filename, sampleRate=12000, segment_duration=None):
    audio = MonoLoader(filename=filename, sampleRate=sampleRate, resampleQuality=4)()

    if segment_duration:
        segment_duration = round(segment_duration*sampleRate)
        segment_start = (len(audio) - segment_duration) // 2
        segment_end = segment_start + segment_duration
    else:
        segment_start = 0
        segment_end = len(audio)

    if segment_start < 0 or segment_end > len(audio):
        raise ValueError('Segment duration is larger than the input audio duration')

    return audio[segment_start:segment_end]


def melspectrogram(audio,
                   sampleRate=12000, frameSize=512, hopSize=256,
                   window='hann', zeroPadding=0, center=True,
                   numberBands=96, lowFrequencyBound=0, highFrequencyBound=None,
                   weighting='linear', warpingFormula='slaneyMel',
                   normalize='unit_tri'):

    if highFrequencyBound is None:
        highFrequencyBound = sampleRate/2

    windowing = Windowing(type=window, normalized=False, zeroPadding=zeroPadding)
    spectrum = Spectrum()
    melbands = MelBands(numberBands=numberBands,
                        sampleRate=sampleRate,
                        lowFrequencyBound=lowFrequencyBound,
                        highFrequencyBound=highFrequencyBound,
                        inputSize=(frameSize+zeroPadding)//2+1,
                        weighting=weighting,
                        normalize=normalize,
                        warpingFormula=warpingFormula,
                        type='power')
    amp2db = UnaryOperator(type='lin2db', scale=2)

    pool = essentia.Pool()
    for frame in FrameGenerator(audio,
                                frameSize=frameSize, hopSize=hopSize,
                                startFromZero=not center):
        pool.add('mel', amp2db(melbands(spectrum(windowing(frame)))))

    return pool['mel'].T


def analyze(audio_file, npy_file, full_audio):
    if full_audio:
      # Analyze full audio duration.
      segment_duration=None
    else:
      # Duration for the Choi's VGG model.
      segment_duration=29.1

    audio = load_audio(audio_file, segment_duration=segment_duration)
    mel = melspectrogram(audio)
    numpy.save(npy_file, mel, allow_pickle=False)
    return


if __name__ == '__main__':
    parser = ArgumentParser(description="Computes a mel-spectrogram for an audio file. Results are stored to a NumPy "
                                        "array binary file.")

    parser.add_argument('audio_file', help='input audio file')
    parser.add_argument('npy_file', help='output NPY file to store mel-spectrogram')
    parser.add_argument('--full', dest='full_audio', help='analyze full audio instead of a centered 29.1s segment',
                        action='store_true')
    args = parser.parse_args()

    analyze(args.audio_file, args.npy_file, args.full_audio)

