"""Midi creator module"""

import math
from collections import Counter

import librosa
import numpy as np
import pretty_midi
from dataclasses import dataclass

from modules.Pitcher.pitcher import get_frequencies_with_high_confidence
from modules.Ultrastar.ultrastar_converter import (
    get_end_time_from_ultrastar,
    get_start_time_from_ultrastar,
    ultrastar_note_to_midi_note,
    midi_note_to_ultrastar_note
)
from modules.console_colors import (
    ULTRASINGER_HEAD,
    red_highlighted,
)
from modules.Ultrastar.ultrastar_txt import UltrastarTxtValue
from modules.Pitcher.pitched_data import PitchedData


def convert_ultrastar_to_midi_instrument(ultrastar_class: UltrastarTxtValue) -> object:
    """Converts an Ultrastar data to a midi instrument"""

    print(f"{ULTRASINGER_HEAD} Creating midi instrument from Ultrastar txt")

    instrument = pretty_midi.Instrument(program=0)
    velocity = 100

    for i in enumerate(ultrastar_class.words):
        pos = i[0]
        start_time = get_start_time_from_ultrastar(ultrastar_class, pos)
        end_time = get_end_time_from_ultrastar(ultrastar_class, pos)
        pitch = ultrastar_note_to_midi_note(int(ultrastar_class.pitches[pos]))

        note = pretty_midi.Note(velocity, pitch, start_time, end_time)
        instrument.notes.append(note)

    return instrument


def instruments_to_midi(instruments: list[object], bpm: float, midi_output: str) -> None:
    """Write instruments to midi file"""

    print(f"{ULTRASINGER_HEAD} Creating midi file -> {midi_output}")

    midi_data = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    for instrument in instruments:
        midi_data.instruments.append(instrument)
    midi_data.write(midi_output)


class MidiCreator:
    """Docstring"""


def convert_frequencies_to_notes(frequency: [str]) -> list[list[str]]:
    """Converts frequencies to notes"""
    notes = []
    for freq in frequency:
        notes.append(librosa.hz_to_note(float(freq)))
    return notes


def most_frequent(array: [str]) -> list[tuple[str, int]]:
    """Get most frequent item in array"""
    return Counter(array).most_common(1)


def find_nearest_index(array: list[float], value: float) -> int:
    """Nearest index in array"""
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (
        idx == len(array)
        or math.fabs(value - array[idx - 1]) < math.fabs(value - array[idx])
    ):
        return idx - 1

    return idx


@dataclass
class MidiSegment:
  note: str
  start: float
  end: float
  word: str


def create_midi_notes_from_pitched_data(start_times: list[float], end_times: list[float], words: list[str], pitched_data: PitchedData) -> list[MidiSegment]:
    """Create midi notes from pitched data"""
    print(f"{ULTRASINGER_HEAD} Creating midi notes from pitched data")

    new_segments = []

    for index, start_time in enumerate(start_times):
        end_time = end_times[index]
        word = str(words[index])

        midi_segment = create_midi_note_from_pitched_data(start_time, end_time, pitched_data, word)

        # Todo: Whats that?
        # segment_count = len(midi_segment)
        # if segment_count > 1:
        #     for index, midi_segment in enumerate(midi_segment[1:]):
        #         midi_segment.word = "~"
        #
        #     if word.endswith(" "):
        #         word = word[:-1]
        #         midi_segment[-1].word += " "
        #
        #midi_segment[0].word = word
        #new_segments.extend(midi_segment)
        new_segments.append(midi_segment)

        # todo: Progress?
        # print(filename + " f: " + str(mean))
    return new_segments


def create_midi_note_from_pitched_data(start_time: float, end_time: float, pitched_data: PitchedData, word: str) -> MidiSegment:
    """Create midi note from pitched data"""

    start = find_nearest_index(pitched_data.times, start_time)
    end = find_nearest_index(pitched_data.times, end_time)

    if start == end:
        freqs = [pitched_data.frequencies[start]]
        confs = [pitched_data.confidence[start]]
    else:
        freqs = pitched_data.frequencies[start:end]
        confs = pitched_data.confidence[start:end]

    conf_f = get_frequencies_with_high_confidence(freqs, confs)

    notes = convert_frequencies_to_notes(conf_f)

    note = most_frequent(notes)[0][0]

    return MidiSegment(note, start_time, end_time, word)

def convert_midi_notes_to_ultrastar_notes(midi_segments: list[MidiSegment]) -> list[int]:
    """Convert midi notes to ultrastar notes"""
    print(f"{ULTRASINGER_HEAD} Creating Ultrastar notes from midi data")

    ultrastar_note_numbers = []
    for i, data in enumerate(midi_segments):
        note_number_librosa = librosa.note_to_midi(data.note)
        pitch = midi_note_to_ultrastar_note(
            note_number_librosa
        )
        ultrastar_note_numbers.append(pitch)
        # todo: Progress?
        # print(
        #    f"Note: {midi_notes[i]} midi_note: {str(note_number_librosa)} pitch: {str(pitch)}"
        # )
    return ultrastar_note_numbers