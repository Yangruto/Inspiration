import numpy as np
import os
import librosa  
import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
from pytube import Playlist, YouTube
import soundfile as sf


def YTallplaylist2mp3(playlist_url, path):
    """
    Download all videos in YT playlist as mp3 to a specific place.
        playlist_url: youtube playlist URL
        path: save position
    """
    playlist_url = playlist_url
    playlist = Playlist(playlist_url)
    urls = playlist.video_urls
    for i in range(0, len(urls)):
        yt = YouTube(urls[i])
        yt.streams.filter().get_audio_only().download(filename=path + f'{i}.mp3')

def audio_prune(path, sr=None):
    """
    Prune an audio then expand one second.
        path: audio path
        sr: sampling rate
    """
    waveform, sampling_rate = librosa.load(path, sr=sr)
    head_not_zero = next(filter(lambda x: x[1] != 0, enumerate(waveform)))[0]
    tail_not_zero = len(waveform) - 1 - next(filter(lambda x: x[1] != 0, enumerate(waveform[::-1])))[0]
    one_second = np.repeat(np.array([0], dtype=np.float32), sampling_rate)
    audio_expand_one_second = np.concatenate([one_second, waveform[head_not_zero:tail_not_zero], one_second])
    return audio_expand_one_second, sampling_rate

if __name__ == "__main__":
    playlist_url = ''
    audio_path = './mp3/'
    YTallplaylist2mp3(playlist_url, audio_path)

    sampling_rate = 0
    audio_list = []
    for file in os.listdir(audio_path):
        if sampling_rate == 0:
            waveform, sampling_rate = audio_prune(audio_path + file, None)
        else:
            waveform, sampling_rate = audio_prune(audio_path + file, sampling_rate)
        audio_list.append(waveform)

    # combine many audios to an audio
    combined_audio = np.concatenate(audio_list)
    # librosa.display.waveshow(combined_audio, sr=sampling_rate)

    sf.write('./mp3/xxx.wav', combined_audio, sampling_rate, subtype='PCM_24')