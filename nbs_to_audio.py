# TODO:
# Add progress reports
# Add logging
# Add looping
# Add fadeout
# Allow exporting layers separately. grouping layers with the same name
# Add different naming conventions for layers

import os
import pydub
import pydub_mixer
import pynbs
import math
from collections import namedtuple
import time
import zipfile
import io


SOUNDS_PATH = "sounds"


default_instruments = [
    "harp.ogg",
    "dbass.ogg",
    "bdrum.ogg",
    "sdrum.ogg",
    "click.ogg",
    "guitar.ogg",
    "flute.ogg",
    "bell.ogg",
    "icechime.ogg",
    "xylobone.ogg",
    "iron_xylophone.ogg",
    "cow_bell.ogg",
    "didgeridoo.ogg",
    "bit.ogg",
    "banjo.ogg",
    "pling.ogg",
]


def load_sound(path):
    return pydub.AudioSegment.from_file(path)


def load_instruments(song, path):
    segments = []

    for ins in default_instruments:
        filename = os.path.join(os.getcwd(), SOUNDS_PATH, ins)
        sound = load_sound(filename)
        segments.append(sound)

    zip_file = None
    for ins in song.instruments:
        # ZipFile object
        if isinstance(path, zipfile.ZipFile):
            zip_file = path
            file = io.BytesIO(zip_file.read(ins.file))
        # File-like object
        elif isinstance(path, str) and os.path.splitext(path)[1] == ".zip":
            zip_file = zipfile.ZipFile(path, "r")
            file = io.BytesIO(zip_file.read(ins.file))
        # File path
        else:
            file = os.path.join(path, ins.file)
        sound = load_sound(file)
        segments.append(sound)

    if zip_file is not None:
        zip_file.close()

    return segments


def sync(sound, channels=2, frame_rate=44100, sample_width=2):
    return (
        sound.set_channels(channels)
        .set_frame_rate(frame_rate)
        .set_sample_width(sample_width)
    )


def change_speed(sound, speed=1.0):
    if speed == 1.0:
        return sound

    new = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    )
    return new.set_frame_rate(sound.frame_rate)


def key_to_pitch(key):
    return 2 ** ((key) / 12)


def vol_to_gain(vol):
    return math.log(max(vol, 0.0001), 10) * 20


class Song(pynbs.File):
    """Extends the pynbs.Song class with some extra functionality."""

    def __init__(self):
        super().__init__()

    def get_pitch(self, note):
        """Returns the detune-aware pitch for a note in the song."""
        key = note.key - 45
        detune = note.pitch / 100
        pitch = key + detune
        return pitch

    def get_volume(self, note, layer):
        """Returns the layer-aware volume for a note in the song."""
        layer_vol = layer.volume / 100
        note_vol = note.velocity / 100
        vol = layer_vol * note_vol
        return vol

    def get_panning(self, note, layer):
        """Returns the layer-aware panning for a note in the song."""
        layer_pan = layer.panning / 100
        note_pan = note.panning / 100
        if layer_pan == 0:
            pan = note_pan
        else:
            pan = (layer_pan + note_pan) / 2
        return pan

    def get_layer_weighted_note(self, note):
        layer = song.layers[note.layer]
        pitch = self.get_pitch(note)
        volume = self.get_volume(note)
        panning = self.get_panning(note)

    def move_note(self, note, offset):
        """Return the same note moved by a certain amount of ticks."""
        new_note = note
        new_note.tick = note.tick + offset
        return new_note

    def __len__(self):
        """Returns the length of the song, in ticks."""
        if self.header.version in (1, 2):
            length = max((note.pitch for note in self.notes))
        else:
            length = self.header.song_length
        return length

    def duration(self, slice):
        """Returns the duration of the song, in milliseconds."""
        # TODO: Make this a @property
        return len(self) / self.header.tempo * 1000

    def __getitem__(self, key):
        if isinstance(key, int):
            section = [note for note in self.notes if note.tick == key]
        elif isinstance(key, slice):
            section = [
                note for note in self.notes if note.tick > start and note.tick < stop
            ]
        else:
            raise TypeError("Index must be an integer")
        return list(section)

    def notes_by_layer(self, group_by_name=False):
        """Returns a dict of lists containing the notes in each non-empty layer of the song."""
        pass

    def loop(self, count):
        start = self.header.loop_start_tick
        notes = self[start:]
        end = len(song)
        for i in range(count):
            offset = len(song) - start
            notes = [self.move_note(note, offset) for note in self.notes]
            self.notes.extend(notes)

    def sorted_notes(self):
        notes = (self.get_layer_weighted_note(note) for note in song.notes)
        return sorted(notes, key=lambda x: (x.pitch, x.instrument, x.volume, x.panning))


class SongRenderer:
    def __init__(self, song, output_path, default_sound):
        pass

    def export():
        pass


def render_audio(
    song,
    output_path,
    custom_sound_path=SOUNDS_PATH,
    loops=0,
    fadeout=False,
    target_bitrate=320,
    target_size=None,
):

    start = time.time()

    instruments = load_instruments(song, custom_sound_path)

    length = len(song)
    track = pydub.AudioSegment.silent(duration=length)
    mixer = pydub_mixer.Mixer()

    last_ins = None
    last_key = None
    last_vol = None
    last_pan = None

    ins_changes = 0
    key_changes = 0
    vol_changes = 0
    pan_changes = 0

    sorted_notes = sort_notes(song)
    for i, note in enumerate(sorted_notes):

        ins = note.instrument
        key = note.pitch
        vol = note.volume
        pan = note.panning

        # TODO: optimize and avoid gain/pitch/key calculation if default value!
        # TODO: ignore locked layers
        # TODO: pan has a loudness compensation? https://github.com/jiaaro/pydub/blob/master/API.markdown#audiosegmentpan

        if ins != last_ins:
            last_key = None
            last_vol = None
            last_pan = None
            sound1 = instruments[note.instrument]
            sound1 = sync(sound1)
            ins_changes += 1

        if key != last_key:
            last_vol = None
            last_pan = None
            pitch = key_to_pitch(key)
            sound2 = change_speed(sound1, pitch)
            key_changes += 1

        if vol != last_vol:
            last_pan = None
            gain = vol_to_gain(vol)
            sound3 = sound2.apply_gain(gain)
            vol_changes += 1

        if pan != last_pan:
            sound4 = sound3.pan(pan)
            sound = sound4
            pan_changes += 1

        last_ins = ins
        last_key = key
        last_vol = vol
        last_pan = pan

        if i % 10 == 0:
            print(
                "Converting note {}/{} (tick: {}, layer: {}, vol: {}, pan: {}, pit: {})".format(
                    i + 1, len(song.notes), note.tick, note.layer, vol, pan, pitch
                )
            )

        pos = note.tick / song.header.tempo * 1000

        mixer.overlay(sound, position=pos)

    track = mixer.to_audio_segment()

    seconds = track.duration_seconds

    if target_size:
        bitrate = (target_size / seconds) * 8
        bitrate = min(bitrate, target_bitrate)
    else:
        bitrate = target_bitrate

    outfile = track.export(
        output_path,
        format="mp3",
        bitrate="{}k".format(bitrate),
        tags={"artist": "test"},
    )

    outfile.close()

    end = time.time()

    with open("tests/log_{}.txt".format(os.path.basename(output_path)), "w") as f:
        f.write(
            "Ins: {}\nKey: {}\nVol: {}\nPan: {}\n\nStart: {}\nEnd: {}\nTime elapsed: {}".format(
                ins_changes,
                key_changes,
                vol_changes,
                pan_changes,
                start,
                end,
                end - start,
            )
        )

