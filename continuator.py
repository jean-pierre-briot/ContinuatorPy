#from packaging.tags import PythonVersion

#!/usr/bin/python
# -*- coding: Unicode -*-

# Continuator in Python
# Version 1.3.1
# Versions/dates: current: 28/08/2025; first: 27/02/2025
# Polyphonic
# Jean-Pierre Briot

# This is a reimplementation in Python of the Continuator from Francois Pachet.
# His original implementation (in 2002, in Java) had unfortunately been lost.
# I tried to reimplement the Continuator from the informations in his publication:
# Pachet, Francois, The Continuator: Musical Interaction with Style, Journal of New Music Research, Volume 32, Issue 3, Pages 333-341, 2003.
# Thanks to Francois for his continuous feedback.

import random
import time
import mido
from mido import MidiTrack, Message, open_input, open_output, get_input_names, get_output_names
import os
import pickle

# constants
_min_midi_pitch = 0
_max_midi_pitch = 128
_max_midi_velocity = 64

#hyperparameters
_player_stop_continuator_start_threshold = 2.0  # Silence duration after which Continuator will start train and generate
_continuator_stop_player_stop_threshold = 15.0  # Silence duration after which Continuator will stop
_max_continuation_length = 50			    # Maximum number of events (= double number of notes) of a continuation
_max_played_notes_considered = 30		    # Maximum last number of played notes considered for training
_max_order = 20                             # Maximum Markov oder (and thus generation length) for each generation of continuation note
_default_generated_note_duration = 0.5	    # Default duration for generated notes (for batch test)
_default_generated_note_velocity = _max_midi_velocity   # Default velocity for generated notes (for batch test)
_key_transposition_semi_tones = 0			# Transposition into N semitones above and N-1 below. If N = 6, this corresponds to a full transposition into the other 11 keys.
                                            # If N = 0, there is no transposition.
                                            # If N >> 6, this corresponds to also transposition into octaves.
                                            # N will be truncated by the max and min MIDI pitch values, thus N is arbitrary
_first_continuation_default_random_generation_mode = True   # Random generation (among continuations) if first note generation fails
_general_default_random_generation_mode = False             # Random generation (among continuations) if any note generation fails
_generation_duration_mode = 'Learnt'        # 3 possible modes for the durations of the continuation notes:
                                            # Learnt: duration of the corresponding matching note learnt,
                                            # Played: duration of the notes played
                                            # Fixed: fixed (_default_fixed_duration) duration
_default_fixed_duration = 0.1               # int in case of 'File' (Midi export) mode

class Note:                                 # Structure of a note
    def __init__(self, pitch, duration, velocity, start_time, delta):
        self.pitch = pitch
        self.duration = duration
        self.velocity = velocity
        self.start_time = start_time
        self.delta = delta      # time delta between this note start time and previous note start time

    def match(self, note):      # Check if current note characteristics (pitch, duration and velocity) is matching some other note (only pitch)
        return note.pitch == self.pitch

class Note_Event:
    def __init__(self, event_type, pitch, velocity, event_time, duration, delta):
        self.event_type = event_type
        self.pitch = pitch
        self.velocity = velocity
        self.event_time = event_time
        self.duration = duration
        self.delta = delta

def note_event_time(note_event):
    return note_event.event_time

def note_sequence_to_pitch_sequence(note_sequence):
    pitch_sequence = []
    for note in note_sequence:
        pitch_sequence.append(note.pitch)
    return pitch_sequence

def pitch_sequence_to_note_sequence(pitch_sequence):    # For Batch test
    note_sequence = []
    for pitch in pitch_sequence:
        note = Note(pitch=pitch, duration=_default_generated_note_duration, velocity=_default_generated_note_velocity, start_time=0, delta=0)
        note_sequence.append(note)
    return note_sequence

class PrefixTreeNode:                       # Structure of a tree node to memorize and index learnt sequences
    def __init__(self):
        self.note = None
        self.children_list = None
        self.continuation_index_list = None

class PrefixTreeContinuator:                # The main class and corresponding algorithms
    def __init__(self):
        self.root_dictionary = {}
        self.continuation_dictionary = {}
        self.continuation_dictionary_current_index = 1
        self.continuation_sequence = []

    def train(self, note_sequence):         # Main entry function lo train the Continuator with a sequence of notes
                                            # note_sequence = [(<pitch_1>, <duration_1>, <velocity_#), ... , (<pitch_N>, <duration_N>, <velocity_N>)]
        self.compute_delta(note_sequence)
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
    def compute_delta(note_sequence):
        for i in range(1, len(note_sequence), 1):
            note_sequence[i].delta = note_sequence[i].start_time - note_sequence[i-1].start_time

    @staticmethod
    def transpose(note_sequence, t):
        transposed_note_sequence = []
        for note in note_sequence:
            new_note = Note(pitch=note.pitch + t, duration=note.duration, velocity=note.velocity, start_time=note.start_time, delta=note.delta)
            transposed_note_sequence.append(new_note)
        return transposed_note_sequence

    def internal_train_without_key_transpose(self, note_sequence):  # Main internal train function
        if not self.root_dictionary and len(note_sequence) <= 1:
            raise RuntimeError('Only one note initially played, thus none continuation can be learnt and therefore generated')
        reversed_note_sequence = note_sequence[::-1]                # [note_N, ... , note_1]
        i = 0                                                       # index of the first item of the reversed played note sequence
        while i < len(reversed_note_sequence) - 1:                  # i will vary from 0 (note_N) to length-1 (note_1)
            sub_reversed_note_sequence = reversed_note_sequence[i:]          # [note_i, ... , note_1]
            continuation_note = sub_reversed_note_sequence[0]       # Continuation_note = note_i
            self.continuation_dictionary[self.continuation_dictionary_current_index] = continuation_note    # Add it to the continuation dictionary
            root_note = sub_reversed_note_sequence[1]               # Second note of the sub sequence is the note to be searched/matched as a root of a tree
            if root_note.pitch not in self.root_dictionary:         # If the note has not yet some corresponding prefix tree root,
                current_node = PrefixTreeNode()                     # then, creation of the corresponding new tree (root)
                self.root_dictionary[root_note.pitch] = current_node
                current_node.note = root_note
                current_node.continuation_index_list = [self.continuation_dictionary_current_index]
            else:                                                   # otherwise, recursive traversal of the tree branches
                current_node = self.root_dictionary[root_note.pitch]
                current_node.continuation_index_list.append(self.continuation_dictionary_current_index) # At first, add the continuation to the continuation list of the root
            for j in range(2, len(sub_reversed_note_sequence), 1):  # Iterative traversal for matching jth level node of the sub reverse input sequence
                                                                    # with a note of the corresponding jth tree branch level children
                                                                    # j will vary from 0 (note_i-2) to i - 2 (note_1),
                                                                    # with note_i : continuation and note_i-1 = root node
                note = sub_reversed_note_sequence[j]
                if current_node.children_list is None:              # If there is no children, then, we have met a terminating leaf,
                    new_child_node = PrefixTreeNode()               # then, we create and insert a new node
                    new_child_node.note = note
                    new_child_node.continuation_index_list = [self.continuation_dictionary_current_index]
                    current_node.children_list = [new_child_node]
                    current_node = new_child_node                   # and continue the iterated traversal
                else:                                               # otherwise,
                    node_exists = False                             # we set up the initial value of a flag to know if we have found a matching node
                    for child_node in current_node.children_list:   # while iterating over the children
                        if child_node.note.match(note):             # This child (exactly) matches
                            child_node.continuation_index_list.append(self.continuation_dictionary_current_index)
                            node_exists = True
                            current_node = child_node               # Next iteration will be on the matching process on this child note
                            break                                   # Successful exit from the children iterative search loop
                    if not node_exists:                             # If no matching node has been found within children,
                        new_child_node = PrefixTreeNode()           # then, we create and insert a new node
                        new_child_node.note = note
                        new_child_node.continuation_index_list = [self.continuation_dictionary_current_index]
                        current_node.children_list.append(new_child_node)
                        current_node = new_child_node
            self.continuation_dictionary_current_index += 1
            i += 1                                                 # Continue the matching search iteration one level down

    def display_memory(self):
         print('Memory:')
         for dummy, root in self.root_dictionary.items():
              self.display_tree(root, 0)

    def display_tree(self, node, level):
        indent = '  ' * level
        print(indent, end='')
        continuation_pitch_list = []
        for i in range(len(node.continuation_index_list)):
            continuation_pitch_list.append(self.continuation_dictionary[node.continuation_index_list[i]].pitch)
        print(str(node.note.pitch) + str(continuation_pitch_list))
        if node.children_list is not None:
            for child in node.children_list:
                self.display_tree(child, level + 1)

    def save_memory(self):
        print('Save memory in file PostMemory.pickle')
        with open('PostMemory.pickle', 'wb') as post_memory_file:
            pickle.dump([self.root_dictionary, self.continuation_dictionary], post_memory_file)

    def read_memory(self):
        if os.path.isfile('PreMemory.pickle'):
            print('Read memory from PreMemory.pickle')
            with open('PreMemory.pickle', 'rb') as pre_memory_file:
                [self.root_dictionary, self.continuation_dictionary] = pickle.load(pre_memory_file)

    def generate(self, input_note_sequence):                              # Generation of a continuation sequence of MIDI messages from an input (played) sequence
        note_sequence = self.generate_note_sequence(input_note_sequence)
        event_sequence = []
        event_time = time.time()
        for note in note_sequence:
            event_time = event_time + note.delta
            event_sequence.append(Note_Event(event_type='note_on', pitch=note.pitch, velocity=note.velocity, event_time=event_time, duration=note.duration, delta=note.delta))
            event_sequence.append(Note_Event(event_type='note_off', pitch=note.pitch, velocity=note.velocity, event_time=event_time + note.duration, duration=note.duration, delta=None))
        event_sequence.sort(key = note_event_time)
        return event_sequence

    def generate_note_sequence(self, note_sequence):
        length_note_sequence = len(note_sequence)                   # Remember length of the played input sequence of notes, because note_sequence will be expanded (append)
        last_input_note = note_sequence[-1]                         # We start with the last note of the reverse sequence: Note_N
        self.continuation_sequence = []                             # Initialization: Assign continuation list to empty list
        matching_child = None                                       # Declaring that flag
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
                current_node = self.root_dictionary[last_input_note.pitch]
                j = 2                                               # Set up j index for a loop for traversing the tree
                                                                    # j is the index of the jth last note of the input sequence
                                                                    # and also the level within the tree
                                                                    # Thus initially, j = 2 : starting with children from the root node to match penultimate note
                while current_node.children_list is not None and j < length_note_sequence:
                                                                    # Iteration to traverse the tree, with at each level (j),
                                                                    # looking for a node matching corresponding note (last jth) of the input sequence
                                                                    # The stop condition is:
                                                                    # a) current node is a leaf (with no children)
                                                                    # or b) j >= length of sequence of notes (i.e. we already parsed all notes of the input sequence)
                    matching_child = None                           # Assign a flag to know if we have found a matching node within children
                    for child in current_node.children_list:        # Iterate over children nodes to look for a node matching jth last note from input sequence
                        if child.note.match(note_sequence[-j]):       # If one matches it
                            matching_child = child                  # then, remember which it is
                            break                                   # and exit from this children iteration loop
                    if matching_child is None:                      # If none of the children matches it,
                        break                                       # then, exit from the traversal to stop the search
                    else:                                           # otherwise, we continue traversing the tree
                        current_node = matching_child               # from current child node
                        j += 1                                      # and down one more level (and previous element of the input sequence)
                if current_node.children_list is None or j >= length_note_sequence or j > _max_order or matching_child is None:
                                                                    # If the search is finished
                                                                    # because:
                                                                    # a) we reached a leaf,
                                                                    # or b) we reached the end of the reverse sequence,
                                                                    # or c) current matching has failed,
                                                                    # then, we create a new continuation note
                    current_node_continuation_index_list = current_node.continuation_index_list
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
    def play_midi_note_event(out_port, event, previous_event):
        if not previous_event:
            sleep_time = 0
        else:
            sleep_time = event.event_time - previous_event.event_time
        time.sleep(sleep_time)
        out_port.send(mido.Message(type=event.event_type, note=event.pitch, velocity=event.velocity))

    def listen_and_continue(self, input_port, output_port):
        with open_input(input_port) as in_port, open_output(output_port) as out_port:
            print('Continuator has started listening on ' + str(input_port) + ' and continuing on ' + str(output_port))
            self.continuation_sequence = []
            is_first_note_played = True
            current_note_on_dict = {}           # key : pitch, value : tuple (note, note_start_time)
            last_note_end_time = time.time()
            continuator_stop_time = None
            played_notes = []
            last_event = None
            while True:                                             # Infinite listening loop
                for event in in_port.iter_pending():
                    if event.type == 'note_on' and event.velocity > 0:
                        if event.note in current_note_on_dict:
                            print('Warning: Note ' + str(note.pitch) + ' has been repeated before being ended')
                            continue
                        else:           # A new note has been played
                            if is_first_note_played:
                                is_fist_note_played = False
                                self.play_all_pending_note_off_events(out_port, self.continuation_sequence)  # to enforce that all still on notes are to be finished
                                self.continuation_sequence = []
                                last_event = None
                                delta = 0
                            else:
                                delta = current_time - previous_note_start_time
                            current_time = time.time()
                            note = Note(pitch=event.note, duration=None, velocity=event.velocity, start_time=current_time, delta=delta)
                            current_note_on_dict[note.pitch] = (note, current_time)
                            played_notes.append(note)
                            previous_note_start_time = current_time
                    elif ((event.type == 'note_off') or (event.type == 'note_on' and event.velocity == 0)) and (event.note in current_note_on_dict):
                        current_time = time.time()                  # A note has been ended
                        (note, note_start_time) = current_note_on_dict[event.note]
                        del current_note_on_dict[event.note]
                        note.duration = current_time - note_start_time
                        last_note_end_time = current_time
                    elif (event.type == 'note_off') or (event.type == 'note_on' and event.velocity == 0):  # An event note_off without previous note_on
                        print('Warning: Event: ' + str(event) + 'with type: ' + str(event.type) + ' and Note: ' + str(event.note) + ' has been finished before being started')
                    # else: Other kind of event (e.g., clock), do nothing
                # Player has stopped playing (at this time)
                player_stop_duration = time.time() - last_note_end_time  # When there is no more played notes pending events
                if self.continuation_sequence:                      # If still continuation note events to be played,
                    current_event = self.continuation_sequence.pop(0)
                    self.play_midi_note_event(out_port=out_port, event=current_event, previous_event=last_event)     # then, play the first one (and remove it)
                    last_event = current_event
                    if not self.continuation_sequence:  # If continuation sequence empty,
                        continuator_stop_time = time.time()  # mark starting time for monitoring end of activity
                elif played_notes and not current_note_on_dict and player_stop_duration > _player_stop_continuator_start_threshold:  # otherwise, if notes have been played, all notes on have been ended, and player has stopped playing
                    self.train(played_notes)                   # then, train from played notes (if any)
                    self.continuation_sequence = self.generate(played_notes[-_max_played_notes_considered:])
                    if not self.continuation_sequence:
                        print("Generation failed.")
                    played_notes = []
                elif continuator_stop_time and time.time() - continuator_stop_time > _continuator_stop_player_stop_threshold:  # If no activity since continuation played and no activity threshold,
                    print('Continuator has stopped after ' + str(_continuator_stop_player_stop_threshold) + ' seconds of player inactivity')
                    break				                            # finish
                else:                                               # otherwise, continue the main loop
                    continue

    def play_all_pending_note_off_events(self, out_port, event_sequence):
        if event_sequence:
            if event_sequence[0]:   # the case of None (empty) first event
                for event in event_sequence:
                    if event.event_type == 'note_off':
                        self.play_midi_note_event(out_port, event, None)

    def batch_test(self, pitch_sequence_list):
        print('Batch test on: ' + str(pitch_sequence_list))
        for pitch_sequence in pitch_sequence_list:
            note_sequence = pitch_sequence_to_note_sequence(pitch_sequence)
            self.train(note_sequence)
            self.display_memory()
            print('Continuation generated: ' + str(note_sequence_to_pitch_sequence(continuator.generate(note_sequence))))

    @staticmethod
    def read_midi_file(midi_file_name):
        midi_sequence = mido.MidiFile(midi_file_name)
        note_sequence = []
        current_note_on_dict = {}
        current_time = 0
        for track in midi_sequence.tracks:
            for event in track:
                current_time += event.time
                if event.type == "note_on" and event.velocity > 0:
                    note = Note(pitch=event.note, duration=None, velocity=event.velocity, start_time=0, delta=0)
                    note_sequence.append(note)
                    if note.pitch in current_note_on_dict:
                        print('Warning: Note ' + str(note.pitch) + ' has been repeated before being ended')
                    current_note_on_dict[note.pitch] = (note, current_time)
                if ((event.type == "note_off") or (event.type == "note_on" and event.velocity == 0)) and (event.note in current_note_on_dict):
                    (note, note_start_time) = current_note_on_dict[event.note]
                    del current_note_on_dict[event.note]
                    note.duration = current_time - note_start_time
        return note_sequence

    @staticmethod
    def write_midi_file(midi_file_name, note_sequence):
            midi_file = mido.MidiFile()
            track = MidiTrack()
            midi_file.tracks.append(track)
            for note in note_sequence:
                track.append(Message(type='note_on', time=0, note=note.pitch, velocity=note.velocity))
                track.append(Message(type='note_off', time=int(note.duration), note=note.pitch, velocity=note.velocity))
            midi_file.save(midi_file_name)

    def run(self, mode):
        self.read_memory()
        match mode:
            case 'RealTime':
                print('MIDI ports available: input: ' + str(mido.get_input_names()) + ' output: ' + str(mido.get_output_names()))  # Display of MIDI ports
                input_port = mido.get_input_names()[0]
                if len(mido.get_output_names()) == 0:            # If there is no output device/software to receive the continuation events output flow,
                    raise RuntimeError('There is no output device to receive the MIDI continuation flow')   # raise en arror
                elif len(mido.get_output_names()) == 1:          # If there is only one MIDI device (and we assume that it has an input - it can produce sound),
                    output_port = mido.get_output_names()[0]    # connect the output port to it (1st output port),
                else:
                    output_port = mido.get_output_names()[1]    # otherwise, connect the output port to the 2nd output port, assuming that it is some software to produce sound (e.g., AppleLogic)
                print('MIDI ports chosen: input: ' + str(input_port) + ' output: ' + str(output_port))  # Display of MIDI ports chosen
                self.listen_and_continue(input_port, output_port)
            case 'File':
                note_sequence = self.read_midi_file('PrePlayed.mid')
                self.train(note_sequence)
                self.continuation_sequence = self.generate(note_sequence[-_max_played_notes_considered:])
                self.write_midi_file('Continuation.mid', self.continuation_sequence)
            case 'Batch':    # Batch test
                self.batch_test([[48, 50, 52, 53], [48, 50, 50, 52], [48, 50], [50, 48], [48]])
        self.save_memory()

# To run it:
continuator = PrefixTreeContinuator()
continuator.run('RealTime')
