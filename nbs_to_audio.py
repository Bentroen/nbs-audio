import os
import pydub
import pynbs


SOUNDS_PATH = "sounds"


instruments = [
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
	"pling.ogg"
]


def load_sound(path):
	return pydub.AudioSegment.from_file(path, format='ogg')


def load_instruments():
	segments = []
	for ins in instruments:
		filename = os.path.join(os.getcwd(), SOUNDS_PATH, ins)
		sound = load_sound(filename)
		segments.append(sound)

	return segments


def render_audio(song, output_path, loops=0, fadeout=False):
	
	instruments = load_instruments()
	
	length = song.header.song_length / song.header.tempo * 1000
	track = pydub.AudioSegment.silent(duration=length)
	
	for i, note in enumerate(song.notes):
		
		if note.instrument > song.header.default_instruments - 1:
			continue
			
		sound = instruments[note.instrument]
		
		pitch = 2**((note.key - 45) / 12)
		pos = note.tick / song.header.tempo * 1000
		
		layer_vol = song.layers[note.layer].volume / 100
		note_vol = note.velocity / 100
		vol = layer_vol * note_vol
		gain = (vol * 100) - 100
		
		layer_pan = song.layers[note.layer].panning
		note_pan = note.panning
		pan = layer_pan * note_pan
		
		print("Converting note {}/{} (tick: {}, vol: {}, pan: {}, pit: {})".format(i+1, len(song.notes), note.tick, vol, pan, pitch))
		
		sound = sound.apply_gain(gain).pan(pan)#.speedup(pitch)
		track = track.overlay(sound, position=pos)
			
			
	
	# Normalize to -3 dBFS
	#track = track.apply_gain(-track.max_dBFS - 3)
	
	
	
	#Fade out
	#track.fade...
	
	file_handle = track.export(output_path,
							   format="mp3",
							   bitrate="320k",
							   tags={"artist": "test"})
						   
	return file_handle