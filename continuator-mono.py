#from packaging.tags import PythonVersion

#!/usr/bin/python
# -*- coding: Unicode -*-

# Continuator in Python
# Version 1.2.2
# Versions/dates: last: 20/03/2025; first: 27/02/2025
# monophonic, batch or real-time mode, richer state/viewpoint (note/pitch, duration, velocity), transposition, tolerance matching
# Jean-Pierre Briot

# This is a reimplementation in Python of the Continuator from François Pachet.
# His original implementation (in 2002, in Java) had unfortunately been lost.
# I tried to reimplement the Continuator from the informations in his publication:
# Pachet, François, The Continuator: Musical Interaction with Style, Journal of New Music Research, Volume 32, Issue 3, Pages 333-341, 2003.
# Thanks to François for his continuous feedback.

import random
import time
import rtmidi
import mido
from mido import MidiFile, MidiTrack, Message, open_input, open_output, get_input_names, get_output_names

# constants
_min_midi_pitch = 0
_max_midi_pitch = 128
_max_midi_velocity = 64

#hyperparameters
_silence_threshold = 2.0					# Silence duration after which Continuator will start train and generate
_max_continuation_length = 30			    # Maximum number of notes of a continuation
_max_played_notes_considered = 10		    # Maximum last number of played notes considered for training
_default_generated_note_duration = 0.5	    # Default duration for generated notes (for batch test)
_default_generated_note_velocity = _max_midi_velocity   # Default velocity for generated notes (for batch test)
_key_transposition_semi_tones = 6			# Transposition into N semitones above and N-1 below. If N = 6, this corresponds to a full transposition into the other 11 keys.
                                            # If N = 0, there is no transposition.
                                            # If N >> 6, this corresponds to also transposition into octaves.
                                            # N will be truncated by the max and min MIDI pitch values, thus N is arbitrary
_first_continuation_default_random_generation_mode = True   # Random generation (among continuations) if first note generation fails
_general_default_random_generation_mode = True             # Random generation (among continuations) if any note generation fails
_train_match_tolerance_dict = {'pitch': 0, 'duration': 2, 'velocity': 64}
_generate_match_tolerance_list = [{'pitch': 0, 'duration': 1, 'velocity': 55}, {'pitch': 2, 'duration': 2, 'velocity': 60}, {'pitch': 4, 'duration': 3, 'velocity': 64}]   # Tolerance (semi-tones below and above) for matching pitch between node and note
_duration_bins = [0.1, 0.3, 1, 10000]
_velocity_bins_number = 3
_velocity_bins_factor = _max_midi_velocity/_velocity_bins_number
_generation_duration_mode = 'Learnt'        # 3 possible modes for the durations of the continuation notes:
                                            # Learnt: duration of the corresponding matching note learnt,
                                            # Played: duration of the notes played
                                            # Fixed: fixed (_default_fixed_duration) duration
_default_fixed_duration = 0.1               # int in case of 'File' (Midi export) mode
_polyphonic_mode = False
_chord_max_notes_on_interval = .5
_chord_min_notes_on_off_interval = .5

class Note:                                 # Structure of a note
    def __init__(self, pitch, duration, velocity):
        self.pitch = pitch
        self.duration = duration
        self.velocity = velocity
        self.binned_duration = None
        self.binned_velocity = round(velocity/_velocity_bins_factor)
        self.is_part_of_a_chord = False

    def compute_duration_bin(self, duration):
        i = 0
        while i < len(_duration_bins) and duration > _duration_bins[i]:
            i += 1
        self.binned_duration = i - 1

    def match_with(self, note, match_tolerance_dict):
#        print('match: p:' + str(self.pitch) + ' d: ' + str(self.duration) + ' bin_d: ' + str(self.binned_duration) + ' v: ' + str(self.velocity) + ' bin_v: ' + str(self.binned_velocity) + ' with p: ' + str(note.pitch) + ' d: ' + str(note.duration) + ' bin_d: ' + str(note.binned_duration) + ' v: ' + str(note.velocity) + ' bin_v: ' + str(note.binned_velocity))
        # raise RuntimeError('Stop match_with')
#        return (note.pitch - match_tolerance_dict['pitch'] <= self.pitch <= note.pitch + match_tolerance_dict['pitch']) and (note.duration - match_tolerance_dict['duration'] <= self.duration <= note.duration + match_tolerance_dict['duration']) and (note.velocity - match_tolerance_dict['velocity'] <= self.velocity <= note.velocity + match_tolerance_dict['velocity'])
        value = (note.pitch - match_tolerance_dict['pitch'] <= self.pitch <= note.pitch + match_tolerance_dict['pitch']) and (note.duration - match_tolerance_dict['duration'] <= self.duration <= note.duration + match_tolerance_dict['duration']) and (note.velocity - match_tolerance_dict['velocity'] <= self.velocity <= note.velocity + match_tolerance_dict['velocity'])
#        print('match: value: ' + str(value))
        return value

def note_sequence_to_pitch_sequence(note_sequence):
    pitch_sequence = []
    for note in note_sequence:
        pitch_sequence.append(note.pitch)
    return pitch_sequence

def pitch_sequence_to_note_sequence(pitch_sequence):    # For Batch test
    note_sequence = []
    for pitch in pitch_sequence:
        note = Note(pitch, _default_generated_note_duration, _default_generated_note_velocity)
        note.compute_duration_bin(note.duration)
        note_sequence.append(note)
    return note_sequence

class PrefixTreeNode:                       # Structure of a tree node to memorize and index learnt sequences
    def __init__(self):
        self.note = None
        self.children_list = None
        self.continuation_index_list = None

    def display(self, prefix_tree_continuator, level):
            indent = '  ' * level
            print(indent, end='')
            continuation_pitch_list = []
            for i in range(len(self.continuation_index_list)):
                continuation_pitch_list.append(prefix_tree_continuator.continuation_dictionary[self.continuation_index_list[i]].pitch)
            print(str(self.note.pitch) + '(' + str(self.note.duration) + '-' + str(self.note.binned_duration) + ', ' + str(self.note.velocity) + '-' + str(self.note.binned_velocity) + ')' + str(continuation_pitch_list))
            if self.children_list is not None:
                for child in self.children_list:
                    child.display(prefix_tree_continuator, level + 1)

class PrefixTreeContinuator:                # The main class and corresponding algorithms
    def __init__(self):
        self.root_dictionary = {}
        self.continuation_dictionary = {}
        self.continuation_dictionary_current_index = 1
        self.current_note_on_dict = None    # Remembering current notes_on which are still on (not off yet)
                                            # key : pitch, value : tuple (note, note_start_time)
        self.first_distinct_note = None
        self.first_distinct_note_start_time = None
        self.last_note_end_time = None
        self.played_notes = []
        self.continuation_sequence = []
        self.chord_notes = []

    def train(self, note_sequence):         # Main entry function lo train the Continuator with a sequence of notes
                                            # note_sequence = [(<pitch_1>, <duration_1>, <velocity_#), ... , (<pitch_N>, <duration_N>, <velocity_N>)]
        self.internal_train_without_key_transpose(note_sequence)    # Train with input sequence
        if _key_transposition_semi_tones > 0:
            note_pitch_sequence = note_sequence_to_pitch_sequence(note_sequence)
            down_iterations_number = min(min(note_pitch_sequence) - _min_midi_pitch, _key_transposition_semi_tones - 1)
            up_iterations_number = min(_max_midi_pitch - max(note_pitch_sequence), _key_transposition_semi_tones)
            i = 1
            while i <= down_iterations_number:
                self.internal_train_without_key_transpose(self.transpose(note_sequence, -i))
                i += 1
            i = 1
            while i <= up_iterations_number:
                self.internal_train_without_key_transpose(self.transpose(note_sequence, i))
                i += 1

    @staticmethod
    def transpose(note_sequence, t):
        transposed_note_sequence = []
        for note in note_sequence:
            new_note = Note(note.pitch + t, note.duration, note.velocity)
            new_note.compute_duration_bin(new_note.duration)
            transposed_note_sequence.append(new_note)
        return transposed_note_sequence

    def internal_train_without_key_transpose(self, note_sequence):  # Main internal train function
        if not self.root_dictionary and len(note_sequence) <= 1:
            raise RuntimeError('Only one note initially played, thus none continuation can be learnt and therefore generated')
        i = len(note_sequence) - 1                                  # index of the last item of the played note sequence
        while i > 0:
                                                                    # i will vary from length-1 (note_N-1) to 0 (note_1)
            note_sub_sequence = note_sequence[:i]                   # Prefix Sub-sequence: [note_1, .. , note_i]
            continuation = note_sequence[i]                         # Continuation = event_i
            self.continuation_dictionary[self.continuation_dictionary_current_index] = continuation
            reversed_note_sub_sequence = note_sub_sequence[::-1]    # Reverse Sub-sequence: [note_i, ..., note_1]
            root_note = reversed_note_sub_sequence[0]               # Last note of the sub sequence note_i is the note to be searched/matched as a root of a tree
            if root_note.pitch not in self.root_dictionary:         # If the note has not yet some corresponding prefix tree root,
                current_node = PrefixTreeNode()                     # then, creation of the corresponding new tree (root)
                self.root_dictionary[root_note.pitch] = [current_node]
                current_node.note = root_note
                current_node.continuation_index_list = [self.continuation_dictionary_current_index]
                # print(1)
                # self.display_memory()
            else:
                node_list = self.root_dictionary[root_note.pitch]
                node_match_exists = False
                for node in node_list:
                    if root_note.match_with(node.note, _train_match_tolerance_dict):
                        node_match_exists = True
                        current_node = node
                        current_node.continuation_index_list.append(self.continuation_dictionary_current_index)  # At first, add the continuation to the continuation list of the root
                        # print(2)
                        # self.display_memory()
                        break
                if not node_match_exists:
                    current_node = PrefixTreeNode()
                    current_node.note = root_note
                    current_node.continuation_index_list = [self.continuation_dictionary_current_index]
                    self.root_dictionary[root_note.pitch].append(current_node)
                    current_node.continuation_index_list.append(self.continuation_dictionary_current_index) # At first, add the continuation to the continuation list of the root
                    # print(3)
                    # self.display_memory()
            for note in reversed_note_sub_sequence[1:]:             # Iterative traversal for matching ith level node of the reverse input sequence
                                                                    # with a note of the corresponding ith tree branch level children
                if current_node.children_list is None:              # If there is no children, then, we have met a terminating leaf,
                    new_child_node = PrefixTreeNode()               # then, we create and insert a new node
                    new_child_node.note = note
                    new_child_node.continuation_index_list = [self.continuation_dictionary_current_index]
                    current_node.children_list = [new_child_node]
                    current_node = new_child_node                   # and continue the iterated traversal
                    # print(4)
                    # self.display_memory()
                else:                                               # otherwise,
                    node_exists = False                             # we set up the initial value of a flag to know if we have found a matching node
                    for node in current_node.children_list:   # while iterating over the children
                        if note.match_with(node.note, _train_match_tolerance_dict):     # This child matches
                            node.continuation_index_list.append(self.continuation_dictionary_current_index)
                            node_exists = True
                            current_node = node               # Next iteration will be on the matching process on this child note
                            break                                   # Successful exit from the children iterative search loop
                    if not node_exists:                             # If no matching node has been found within children,
                        new_child_node = PrefixTreeNode()           # then, we create and insert a new node
                        new_child_node.note = note
                        new_child_node.continuation_index_list = [self.continuation_dictionary_current_index]
                        current_node.children_list.append(new_child_node)
                        current_node = new_child_node
                        # print(5)
                        # self.display_memory()
            self.continuation_dictionary_current_index += 1
            i += -1                                                 # Continue the matching search iteration one level down

    def display_memory(self):
        print('Memory:')
        for dummy, root_list in self.root_dictionary.items():
            for root in root_list:
                root.display(self, 0)

    def generate(self, note_sequence):                              # Generation of a continuation
        length_note_sequence = len(note_sequence)                   # Remember length of the played input sequence of notes, because note_sequence will be expanded (append)
        last_input_note = note_sequence[-1]                         # We start with the last note of the reverse sequence: Note_N
        self.continuation_sequence = []                             # Initialization: Assign continuation list to empty list
        chosen_node = None
        matching_node_list = None
        for i in range(1, _max_continuation_length):
            ii = i
            if last_input_note.pitch not in self.root_dictionary:   # If there is no matching tree root thus we cannot generate a continuation
                if _general_default_random_generation_mode:         # If default random generation mode
                    next_note = self.continuation_dictionary[random.randint(1, len(self.continuation_dictionary))]
                    note_sequence.append(next_note)                 # Add this continuation note to the list of input notes
                    self.continuation_sequence.append(next_note)    # Add this continuation note to the list of continuations
                    last_input_note = next_note                     # And continue the generation from this (new) last note
                elif i == 1 and _first_continuation_default_random_generation_mode:
                    next_note = self.continuation_dictionary[random.randint(1, len(self.continuation_dictionary))]
                    match _generation_duration_mode:
                        # case 'Learnt':                            If Learnt duration, do nothing specific
                        case 'Played':
                            if ii > len(note_sequence):
                                ii = i - len(note_sequence)
                            next_note.duration = note_sequence[ii - 1].duration
                        case 'Fixed':
                            next_note.duration = _default_fixed_duration
                    note_sequence.append(next_note)                 # Add this continuation note to the list of input notes
                    self.continuation_sequence.append(next_note)    # Add this continuation note to the list of continuations
                    last_input_note = next_note                     # And continue the generation from this (new) last note
                else:                                               # Otherwise, no continuation possible,
                    break                                           # and we exit from loop
            else:                                                   # Otherwise,
                current_node_list = self.root_dictionary[last_input_note.pitch]
                matching_node_list = []
                for match_tolerance_dict in _generate_match_tolerance_list:
                    for node in current_node_list:
                        if last_input_note.match_with(node.note, match_tolerance_dict):
                            matching_node_list.append(node)
                    if not matching_node_list:
                        break
                if not matching_node_list:
                    break
                else:
#                    print('matching_node_list: ' + str(matching_node_list))
                    chosen_node = matching_node_list[random.randint(0, len(matching_node_list) -1)]
                    j = 2                                               # Set up j index for a loop for traversing the tree
                                                                    # j is the index of the jth last note of the input sequence
                                                                    # and also the level within the tree
                                                                    # Thus initially, j = 2 : starting with children from the root node to match penultimate note
                    while chosen_node.children_list is not None and j < length_note_sequence:
                        for match_tolerance_dict in _generate_match_tolerance_list:
                                                                    # Iteration to traverse the tree, with at each level (j),
                                                                    # looking for a node matching corresponding note (last jth) of the input sequence
                                                                    # The stop condition is:
                                                                    # a) current node is a leaf (with no children)
                                                                    # or b) j >= length of sequence of notes (i.e. we already parsed all notes of the input sequence)
                            matching_child_node_list = []                   # Assign a flag to know if we have found a matching node within children
                            for node in chosen_node.children_list:        # Iterate over children nodes to look for a node matching jth last note from input sequence
                                if note_sequence[-j].match_with(node.note, match_tolerance_dict):       # If one matches it (with default tolerance)
                                    matching_child_node_list.append(node)
                            if not matching_child_node_list:
                                break
                        if not matching_child_node_list:              # If none of the children matches it,
                            break                                       # then, exit from the traversal to stop the search
                        else:                                           # otherwise, we continue traversing the tree
#                            print('matching_child_node_list: ' + str(matching_child_node_list))
                            chosen_node = matching_child_node_list[random.randint(0, len(matching_child_node_list) - 1)]
                                                                        # from current child node
                            j += 1                                      # and down one more level (and previous element of the input sequence)
                if chosen_node.children_list is None or j >= length_note_sequence or matching_child_node_list is None:
                                                                    # If the search is finished
                                                                    # because:
                                                                    # a) we reached a leaf,
                                                                    # or b) we reached the end of the reverse sequence,
                                                                    # or c) current matching has failed,
                                                                    # then, we create a new continuation note
                    current_node_continuation_index_list = chosen_node.continuation_index_list
                    next_note = self.continuation_dictionary[current_node_continuation_index_list[random.randint(0, len(current_node_continuation_index_list) -1)]]
                                                                    # by sorting within current node list of continuations
                                                                    # as there may have several occurrences of the same note,
                                                                    # this implements the probabilities of a Markov model
                    match _generation_duration_mode:
                        # case 'Learnt':                            If Learnt duration, do nothing specific
                        case 'Played':
                            if ii > len(note_sequence):
                                ii = i - len(note_sequence)
                            next_note.duration = note_sequence[ii - 1].duration
                        case 'Fixed':
                            next_note.duration = _default_fixed_duration
                    note_sequence.append(next_note)                 # Add this continuation note to the list of input notes
                    self.continuation_sequence.append(next_note)    # Add this continuation note to the list of continuations
                    last_input_note = next_note                     # And continue the generation from this (new) last note
        return self.continuation_sequence

    @staticmethod
    def play_midi_note(port_name, note):
        with open_output(port_name) as output:
            output.send(mido.Message('note_on', note = note.pitch, velocity = note.velocity))
            time.sleep(note.duration)
            output.send(mido.Message('note_off', note = note.pitch, velocity = note.velocity))

    def play_midi_chord(port_name, note_list):
        with open_output(port_name) as output:
            for note in note_list:
                output.send(mido.Message('note_on', note=note.pitch, velocity=note_list[0].velocity))
            time.sleep(note_list[0].duration)
            for note in note_list:
                output.send(mido.Message('note_off', note=note.pitch, velocity=note_list[0].velocity))

    def listen_and_continue(self, input_port, output_port):
        with mido.open_input(input_port) as in_port, mido.open_output(output_port) as dummy:
            print('Currently listening on ' + str(input_port))
            self.continuation_sequence = []
            self.first_distinct_note = None
            self.first_distinct_note_start_time = None
            self.current_note_on_dict = {}
            self.last_note_end_time = time.time()
            while True:                                             # Infinite listening loop
                for event in in_port.iter_pending():
                    if event.type == 'note_on' and event.velocity > 0:
                        if event.note in self.current_note_on_dict:
                            print('Warning: Note ' + str(note.pitch) + ' has been repeated before being ended')
                            continue
                        else:
                            self.continuation_sequence = []             # A new note has been played
                            note = Note(event.note, None, event.velocity)
                            current_time = time.time()
                            if _polyphonic_mode:
                                if not(self.current_note_on_dict):
                                    self.first_distinct_note = note
                                elif (current_time - self.first_distinct_note_start_time) <= _chord_max_notes_on_interval:
                                    self.current_note_on_dict[note.pitch] = (note, current_time)
                            else:
                                self.current_note_on_dict[note.pitch] = (note, current_time)
#                            print('New Note: pitch: ' + str(note.pitch) + ' binned_velocity: ' + str(note.binned_velocity))
                            self.played_notes.append(note)
                    elif ((event.type == 'note_off') or (event.type == 'note_on' and event.velocity == 0)) and (event.note in self.current_note_on_dict):
                        current_time = time.time()                  # A note has been ended
                        if _polyphonic_mode:
                            if event.note == self.first_distinct_note.pitch:
                                self.first_distinct_note.is_part_of_a_chord = True
                                for (note, start_time) in self.current_note_on_dict.values:
                                    if current_time - start_time > _chord_min_notes_on_off_interval:
                                        note.is_part_of_a_chord = True
                        (note, note_start_time) = self.current_note_on_dict[event.note]
                        del self.current_note_on_dict[event.note]
                        note.duration = current_time - note_start_time
                        note.compute_duration_bin(note.duration)
                        self.last_note_end_time = current_time
                silence_duration = time.time() - self.last_note_end_time    # When there is no more played notes pending events
                if self.continuation_sequence:                      # If still continuation notes to be played,
                    if _polyphonic_mode:
                        if self.continuation_sequence[O].is_part_of_a_chord:
                            self.chord_notes.append(self.continuation_sequence.pop(O))
                            i = 0
                            while self.continuation_sequence:
                                if note.is_part_of_a_chord:
                                    self.chord_notes.append(self.continuation_sequence.pop(O))
                                    i += 1
                                else:
                                    break
                        self.play_midi_chords(output_port, self.self.chord_notes)
                    else:
                        self.play_midi_note(output_port, self.continuation_sequence.pop(0))     # then, play the first one (and remove it)
                elif self.played_notes and not self.current_note_on_dict and silence_duration > _silence_threshold:     # otherwise, if notes have been played, all notes on have been ended, and player has stopped playing
                    self.train(self.played_notes)                   # then, train from played notes (if any)
                    self.continuation_sequence = self.generate(self.played_notes[-_max_played_notes_considered:])
                    if not self.continuation_sequence:
                        print("Generation failed.")
                    self.played_notes = []
                else:                                               # otherwise, continue the main loop
                    continue

    def batch_test(self, pitch_sequence_list):
        for pitch_sequence in pitch_sequence_list:
            note_sequence = pitch_sequence_to_note_sequence(pitch_sequence)
#            for note in note_sequence:
#                print(str(note.pitch) + '(' + str(note.binned_duration) + ', ' + str(note.binned_velocity) + ')')
            self.train(note_sequence)
            self.display_memory()
            print('Continuation generated: ' + str(note_sequence_to_pitch_sequence(continuator.generate(note_sequence))))

    def read_midi_file(self, midi_file_name):
        midi_sequence = mido.MidiFile(midi_file_name)
        note_sequence = []
        self.current_note_on_dict = {}
        current_time = 0
        for track in midi_sequence.tracks:
            for event in track:
                current_time += event.time
                if event.type == "note_on" and event.velocity > 0:
                    note = Note(event.note, None, event.velocity)
                    note_sequence.append(note)
                    if note.pitch in self.current_note_on_dict:
                        print('Warning: Note ' + str(note.pitch) + ' has been repeated before being ended')
                    self.current_note_on_dict[note.pitch] = (note, current_time)
                if ((event.type == "note_off") or (event.type == "note_on" and event.velocity == 0)) and (event.note in self.current_note_on_dict):
                    (note, note_start_time) = self.current_note_on_dict[event.note]
                    del self.current_note_on_dict[event.note]
                    note.duration = current_time - note_start_time
        return note_sequence

    @staticmethod
    def write_midi_file(midi_file_name, note_sequence):
            midi_file = mido.MidiFile()
            track = MidiTrack()
            midi_file.tracks.append(track)
            for note in note_sequence:
                track.append(Message('note_on', time=0, note=note.pitch, velocity=note.velocity))
                track.append(Message('note_off', time=int(note.duration), note=note.pitch, velocity=note.velocity))
            midi_file.save(midi_file_name)

    def run(self, mode):
        match mode:
            case 'RealTime':
                print('MIDI ports available: ' + str(mido.get_input_names()))  # Display of MIDI ports
                input_port = mido.get_input_names()[0]
                output_port = mido.get_output_names()[0]
                self.listen_and_continue(input_port, output_port)
            case 'File':
                note_sequence = self.read_midi_file('Test.mid')
                self.train(note_sequence)
                self.continuation_sequence = self.generate(note_sequence[-_max_played_notes_considered:])
                self.write_midi_file('Continuation.mid', self.continuation_sequence)
            case 'Batch':    # Batch test
                self.batch_test([[48, 50, 52, 53], [48, 50, 50, 52], [48, 50], [50, 48], [48]])

continuator = PrefixTreeContinuator()
continuator.run('RealTime')
