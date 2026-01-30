#from packaging.tags import PythonVersion

#!/usr/bin/python
# -*- coding: Unicode -*-

# Metrics for music in Python
# Version 1.1.3
# Versions/dates: current: 29/01/2026; first: 27/12/2025
# Jean-Pierre Briot

# Metrics for evaluating music played (MIDI)

import math
import zlib
from collections import Counter
import matplotlib.pyplot as plt
from chordify import chordify, pitch_sequence_to_pnote_sequence

def shannon_entropy(sequence, base=2):
    if not sequence:
        return 0.0
    counts = Counter(sequence)
    length = len(sequence)
    probabilities = [count / length for count in counts.values()]
    entropy = -sum(p * math.log(p, base) for p in probabilities)
    return entropy

def kolmogorov_complexity(sequence):
    bytes_string = str(sequence).encode('utf-8')
    k_length = len(zlib.compress(bytes_string))
    return k_length, k_length / len(sequence)

_saved_played_notes_list = []

_metrics_history = {'length': [], 'pitch_min': [], 'pitch_max': [], 'duration_min': [], 'duration_max': [], 'velocity_min': [], 'velocity_max': [],
                    'entropy': [], 'chroma_entropy': [], 'complexity': [], 'chroma_complexity': [],'compression_ratio': [], 'chroma': []}


def note_sequence_to_pitch_sequence(note_sequence):
    pitch_sequence = []
    for note in note_sequence:
        pitch_sequence.append(note.pitch)
    return pitch_sequence

def note_sequence_to_duration_sequence(note_sequence):
    duration_sequence = []
    for note in note_sequence:
        duration_sequence.append(note.duration)
    return duration_sequence

def note_sequence_to_velocity_sequence(note_sequence):
    velocity_sequence = []
    for note in note_sequence:
        velocity_sequence.append(note.velocity)
    return velocity_sequence

def save_played_notes(played_notes):
    _saved_played_notes_list.append(played_notes)

def compute_metrics(pitch_sequence, duration_sequence, velocity_sequence):
    chroma_sequence = []
    for pitch in pitch_sequence:
        chroma_sequence.append(pitch%12)
    entropy = shannon_entropy(pitch_sequence)
    (complexity, compression_ratio) = kolmogorov_complexity(pitch_sequence)
    chroma_entropy = shannon_entropy(chroma_sequence)
    (chroma_complexity, chroma_compression_ratio) = kolmogorov_complexity(chroma_sequence)
    chroma_stats = compute_chroma(pitch_sequence, duration_sequence)
    _metrics_history['length'].append(len(pitch_sequence))
    _metrics_history['pitch_min'].append(min(pitch_sequence))
    _metrics_history['pitch_max'].append(max(pitch_sequence))
    _metrics_history['duration_min'].append(min(duration_sequence))
    _metrics_history['duration_max'].append(max(duration_sequence))
    _metrics_history['velocity_min'].append(min(velocity_sequence))
    _metrics_history['velocity_max'].append(max(velocity_sequence))
    _metrics_history['entropy'].append(entropy)
    _metrics_history['chroma_entropy'].append(chroma_entropy)
    _metrics_history['complexity'].append(complexity)
    _metrics_history['chroma_complexity'].append(chroma_complexity)
    _metrics_history['compression_ratio'].append(compression_ratio)
    _metrics_history['chroma'].append(chroma_stats)

_chroma_index_list = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

_chroma_midi_pitch_index_list = list(range(60, 72))

def compute_chroma(pitch_sequence, duration_sequence):
    chroma_duration_dict = dict(zip(_chroma_index_list, [0.] * len(_chroma_index_list)))
    for i in range(0, len(pitch_sequence)):
         pitch = pitch_sequence[i]
         chroma = _chroma_index_list[pitch%12]
         chroma_duration_dict[chroma] = chroma_duration_dict[chroma] + duration_sequence[i]
    total_duration = 0
    for key in chroma_duration_dict:
         total_duration = total_duration + chroma_duration_dict[key]
    for key in chroma_duration_dict:
         chroma_duration_dict[key] = chroma_duration_dict[key] / total_duration
    return chroma_duration_dict

def display_metrics_history():
    print('Starting computing metrics')
    for note_sequence in _saved_played_notes_list:
        compute_metrics(note_sequence_to_pitch_sequence(note_sequence), note_sequence_to_duration_sequence(note_sequence), note_sequence_to_velocity_sequence(note_sequence))
    x_list = []
    for i in range(1, len(_metrics_history['length']) + 1):
        x_list.append([i])
    fig, (ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9) = plt.subplots(1, 9)
    ax1.plot(x_list, _metrics_history['length'], color='green')
    ax1.set_title('Number\nof Notes', color='green')
    ax1.tick_params(axis='x')
    ax2.plot(x_list, _metrics_history['pitch_min'], color='blue')
    ax2.plot(x_list, _metrics_history['pitch_max'], color='blue')
    ax2.set_title('Notes\nRange', color='blue')
    ax3.plot(x_list, _metrics_history['duration_min'], color='magenta')
    ax3.plot(x_list, _metrics_history['duration_max'], color='magenta')
    ax3.set_title('Duration\nRange', color='magenta')
    ax4.plot(x_list, _metrics_history['velocity_min'], color='cyan')
    ax4.plot(x_list, _metrics_history['velocity_max'], color='cyan')
    ax4.set_title('Velocity\nRange', color='cyan')
    ax5.plot(x_list, _metrics_history['entropy'], color='red')
    ax5.set_title('Notes\nEntropy', color='red')
    ax6.plot(x_list, _metrics_history['chroma_entropy'], color='orange')
    ax6.set_title('Chroma\nEntropy', color='orange')
    ax7.plot(x_list, _metrics_history['complexity'], color='black')
    ax7.set_title('Notes\nComplexity', color='black')
    ax8.plot(x_list, _metrics_history['chroma_complexity'], color='brown')
    ax8.set_title('Chroma\nComplexity', color='brown')
    ax9.plot(x_list, _metrics_history['compression_ratio'], color='grey')
    ax9.set_title('Notes\nCompression %', color='grey')
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    y_list = list(range(0, len(_metrics_history['length'])))
    chord_list = []
    for y in y_list:
        ys = list(_metrics_history['chroma'][y].values())
        index_list = indexes_of_n_first_greatest_values(ys, 3)
        pitch_list = []
        for i in index_list:
            pitch_list.append(_chroma_midi_pitch_index_list[i])
        pitch_list.sort()
        pnote_list = pitch_sequence_to_pnote_sequence(pitch_list)
        chord = chordify(pnote_list)
        chord_list.append(chord)
    print('chord_list: ' + str(chord_list))
    for y in y_list:
        xs = _chroma_index_list
        ys = list(_metrics_history['chroma'][y].values())
        ax.bar(xs, ys, zs=y, zdir='y')
    ax.set_xlabel('Chroma')
    ax.set_ylabel('Turns')
    ax.set_zlabel('%')
    ax.set_yticks(y_list)
    plt.show()

def indexes_of_n_first_greatest_values(l, n):
    index_list = []
    for i in range(0, n):
        vmax = 0
        vmax_index = 0
        for j in range(0, len(l)):
            if l[j] > vmax:
                vmax = l[j]
                vmax_index = j
        index_list.append(vmax_index)
        l[vmax_index] = 0.
    return index_list

def test_metrics():
    #compute_metrics([69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80], [1]* 12, [64,] * 12)
    #compute_metrics([69, 70, 70, 70], [1]*4, [64]*4)
    compute_metrics([69, 65, 69, 65], [1, 1, 1, 1], [64, 32, 16, 64])
    compute_metrics([69, 65, 69, 67, 69], [1, 0.5, 1, 0.25, 1], [64, 32, 16, 64, 32])
    #compute_metrics([65, 69, 65, 67], [1, 0.5, 1, 0.5], [64, 16, 32, 16])
    #compute_metrics([63, 65, 63, 65, 63, 63], [1, 0.5, 1, 0.25, 1, 0.5], [32, 64, 64, 32, 32, 32])
    #compute_metrics([69, 65, 67], [1, 0.5, 0.5], [32, 16, 64])
    display_metrics_history()

#test_metrics()

#print(shannon_entropy([69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80]))
#print(shannon_entropy([69, 70, 70, 70]))

