from packaging.tags import PythonVersion

#!/usr/bin/python
# -*- coding: Unicode -*-

# Continuator in Python
# Version 1.2
# monophonic, batch or real-time mode, richer state/viewpoint (note/pitch, duration, velocity), transposition, tolerance matching
# 27/02/2025
# Jean-Pierre Briot

# This is a reimplementation in Python of the Continuator from François Pachet.
# His original implementation (in 2002, in Java) had unfortunately been lost.
# I tried to reimplement the Continuator from the informations in his publication:
# Pachet, François, The Continuator: Musical Interaction with Style, Journal of New Music Research, Volume 32, Issue 3, Pages 333-341, 2003.
# Thanks to François for his continuous feedback.

import time
import random
import mido
from mido import MidiFile, MidiTrack, Message, open_input, open_output, get_input_names, get_output_names

#hyperparameters
_silence_threshold = 2.0					# Silence duration after which continuator will start train and generate
_max_continuation_length = 20				# Maximum number of notes of a continuation
_max_played_notes_considered = 20		    # Maximum last number of played notes considered for training
_default_generated_note_duration = 0.5	    # Default duration for generated notes
_default_generated_note_velocity = 64		# Default velocity for generated notes
_after_continuation_sleep = 0.1             # Sleep duration after having played continuation
_key_transposition_mode = True			    # Transposition into 12 keys/tonalities
_octave_transposition_number = 0		    # Transposition into N octaves below and above (within the MIDI pitch note range)
_first_continuation_default_random_generation_mode = True   # Random generation (among continuations) if first note generation fails
_general_default_random_generation_mode = False             # Random generation (among continuations) if any note generation fails
_match_pitch_interval_tolerance = 2         # Tolerance (semi-tones below and above) for matching pitch between node and note
_duration_discretization = 1

class Note:                                 # Structure of a note
    def __init__(self, pitch, duration, velocity):  # Instance variables: <pitch>, <duration, <velocity>
        self.pitch = pitch                  # Pitch
        self.duration = duration            # Duration
        self.velocity = velocity            # Velocity

def create_note_sequence(pitch_sequence):
    note_sequence = []
    for pitch in pitch_sequence:
        note = Note(pitch, _default_generated_note_duration, _default_generated_note_velocity)
        note_sequence.append(note)
    return note_sequence

def pitch_sequence_from_note_sequence(note_sequence):
    pitch_sequence = []
    for note in note_sequence:
        pitch_sequence.append(note.pitch)
    return pitch_sequence

def current_note_on_tuple_pitch_list(current_note_on_tuple_list):
        note_pitch_list = []
        for note_tuple in current_note_on_tuple_list:
            note_pitch_list.append(note_tuple[0])
        return(note_pitch_list)

class PrefixTreeNode:                       # Structure of a tree node to memorize and index learnt sequences
    def __init__(self):                     # Instance variables: <note>, <children_list>, <continuation_index_list>
        self.note = None                    # Corresponding note
        self.children_list = None           # List of children nodes
        self.continuation_index_list = None # List of indexes of continuations
                                            # Default values = None, in order to know for instance when a node is a terminal leaf (no children/subtree)
    def match(self, note, tolerance):                  # Check if current node characteristics (e.g., its corresponding note pitch) is matching some note characteristics (e.g., that note pitch)
        return self.note.pitch in range(note.pitch - tolerance, note.pitch + tolerance + 1)

class PrefixTreeContinuator:                # The main class and corresponding algorithms
    def __init__(self):
        self.root_dictionary = {}           # Root tree dictionary
        self.continuation_dictionary = {}   # Continuation dictionary
        self.continuation_dictionary_current_index = 1  # Remembering the number of continuation index to be increased after each new continuation indexed
        self.current_note_on_dict = None    # Remembering current notes_on which are still on (not off yet)
                                            # key : pitch, value : tuple (note, note_start_time)
        self.last_note_end_time = None      # Remembering last note end time
        self.played_notes = []              # List of input (played) notes
        self.continuation_sequence = []

    def train(self, note_sequence):         # Main entry function lo train the continuator with a sequence of notes
                                            # note_sequence = [(<pitch_1>, <duration_1>, <velocity_#), ... , (<pitch_N>, <duration_N>, <velocity_N>)]
        self.internal_train_without_key_transpose(note_sequence)    # Train with input sequence
        if _key_transposition_mode:         # If key transposition,
            for i in range(-5, 0):          # then, transpose pitches of all notes of the sequence in half-tone above and below upto half-octave
                self.internal_train_without_key_transpose(self.transpose(note_sequence, i))
            for i in range(1, 7):
                self.internal_train_without_key_transpose(self.transpose(note_sequence, i))

    def internal_train_without_key_transpose(self, note_sequence):
                                            # Internal train function
        self.internal_train_without_any_transpose(note_sequence)    # Train with input sequence
        if _octave_transposition_number > 0:  # If octave transposition,
            note_pitch_sequence = []
            for note in note_sequence:      # then, transpose pitches of all notes of the sequence in octaves within MIDI pitches limits [O, 128]
                note_pitch_sequence.append(note.pitch)
            max_pitch = max(note_pitch_sequence)
            i = 1
            while i <= _octave_transposition_number and max_pitch + (i * 12) <= 128:
                self.internal_train_without_any_transpose(self.transpose(note_sequence, i * 12))
                i += 1
            min_pitch = min(note_pitch_sequence)
            i = -1
            while i <= _octave_transposition_number and min_pitch + (i * 12) >= 0:
                self.internal_train_without_any_transpose(self.transpose(note_sequence, i * 12))
                i += -1
 
    @staticmethod
    def transpose(note_sequence, t):        # Transpose pitches of all notes of the sequence in some offset
        transposed_note_sequence = []
        for note in note_sequence:
            new_note = Note(note.pitch + t, note.duration, note.velocity)
            transposed_note_sequence.append(new_note)
        return transposed_note_sequence

    def internal_train_without_any_transpose(self, note_sequence):  # Main internal train function
        if not self.root_dictionary and len(note_sequence) <= 1:         # If memory empty and played sequence contains only one note or none,
            raise RuntimeError('Only one note initially played, thus no continuation may be learnt and therefore generated')   # then, no continuation can be learnt anf therefore (cannot be) generated
        i = len(note_sequence) - 1   # index of the last item of the played note sequence
        while i > 0:                                                # Iterative matching of the successive notes (events) of the played sequence
                                                                    # i will vary from length-1 (note_N-1) to 0 (note_1)
         # for k in range(len(note_sequence) - 1, -1 - 1):          Does not work correctly (?), thus substituted by a while loop
            note_sub_sequence = note_sequence[:i]                   # Prefix Sub-sequence: [note_1, .. , note_i]
            continuation = note_sequence[i]                         # Continuation = event_i
            self.continuation_dictionary[self.continuation_dictionary_current_index] = continuation
            reversed_note_sub_sequence = note_sub_sequence[::-1]    # Reverse Sub-sequence: [note_i, ..., note_1]
            root_note = reversed_note_sub_sequence[0]               # Last note of the sub sequence note_i is the note to be searched/matched as a root of a tree
            if root_note.pitch not in self.root_dictionary:         # If the note has not yet some corresponding prefix tree root,
                current_node = PrefixTreeNode()                     # then, creation of the corresponding new tree (root)
                self.root_dictionary[root_note.pitch] = current_node
                current_node.note = root_note
                current_node.continuation_index_list = [self.continuation_dictionary_current_index]
            else:                                                   # Otherwise, recursive traversal of the tree branches
                current_node = self.root_dictionary[root_note.pitch]
                current_node.continuation_index_list.append(self.continuation_dictionary_current_index) # At first, add the continuation to the continuation list of the root
            for note in reversed_note_sub_sequence[1:]:             # Iterative traversal for matching ith level node of the reverse input sequence
                                                                    # with a note of the corresponding ith tree branch level children
                if current_node.children_list is None:              # If there is no children, we have met a terminating leaf,
                    new_child_node = PrefixTreeNode()               # then, we create and insert a new node
                    new_child_node.note = note
                    new_child_node.continuation_index_list = [self.continuation_dictionary_current_index]
                    current_node.children_list = [new_child_node]
                    current_node = new_child_node                   # And continue the iterated traversal
                else:                                               # Otherwise
                    node_exists = False                             # Setting up the initial value of a flag to know if we have found a matching node
                    for child_node in current_node.children_list:   # while iterating over the children
                        if child_node.match(note, 0):               # This child (exactly) matches
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
            i += -1                                                 # Continue the matching search iteration one level down

    def display_memory(self):                                       # To display the list of the trees within the memory
         print('Memory:')
         for dummy, root in self.root_dictionary.items():
              self.display_tree(root, 0)                        # Calling a recursive display of the tree

    def display_tree(self, node, level):                            # Recursive display of a tree nodes (corresponding notes and continuations)
        indent = '  ' * level                                       # Showing number of indentations corresponding to the level of the node
        print(indent, end='')
        continuation_pitch_list = []
        for i in range(len(node.continuation_index_list)):
            continuation_pitch_list.append(self.continuation_dictionary[node.continuation_index_list[i]].pitch)
        print(str(node.note.pitch) + str(continuation_pitch_list))
        if node.children_list is not None:
            for child in node.children_list:
                self.display_tree(child, level + 1)

    def generate(self, note_sequence):                              # Generation of a continuation
        length_note_sequence = len(note_sequence)                   # Remember length of the sequence of notes, because will be used iteratively
        last_input_note = note_sequence[-1]                         # We start with the last note of the reverse sequence: Note_N
        self.continuation_sequence = []                             # Initialization: Assign continuation list to empty list
        matching_child = None                                       # Declaring that flag
        for i in range(1, _max_continuation_length):
            if last_input_note.pitch not in self.root_dictionary:   # If there is no matching tree root thus we cannot generate a continuation
                                                                    # if default random generation mode
                if _general_default_random_generation_mode:
                    next_note = self.continuation_dictionary[random.randint(1, len(self.continuation_dictionary))]
                    note_sequence.append(next_note)                 # Add this continuation note to the list of input notes
                    self.continuation_sequence.append(next_note)    # Add this continuation note to the list of continuations
                    last_input_note = next_note                     # And continue the generation from this (new) last note
                elif i == 1 and _first_continuation_default_random_generation_mode:
                    # print('generate: self.continuation_dictionary: ' + str(self.continuation_dictionary))
                    next_note = self.continuation_dictionary[random.randint(1, len(self.continuation_dictionary))]
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
                        if child.match(note_sequence[-j], _match_pitch_interval_tolerance):
                                                                    # If one matches it (with default tolerance)
                            matching_child = child                  # then, remember which it is
                            break                                   # and exit from this children iteration loop
                    if matching_child is None:                      # If none of the children matches it,
                        break                                       # then, exit from the traversal to stop the search
                    else:                                           # otherwise, we continue traversing the tree
                        current_node = matching_child               # from current child node
                        j += 1                                      # and down one more level (and previous element of the input sequence)
                if current_node.children_list is None or j >= length_note_sequence or matching_child is None:
                                                                    # If the search is finished
                                                                    # because:
                                                                    # a) we reached a leaf
                                                                    # or b) we reached the end of the reverse sequence
                                                                    # or c) current matching has failed
                                                                    # the, we create a new continuation note
                    current_node_continuation_index_list = current_node.continuation_index_list
                    # print('generate: current_node.note.pitch: ' + str(current_node.note.pitch) + ' current_node_continuation_index_list: ' + str(current_node_continuation_index_list))
                    next_note = self.continuation_dictionary[current_node_continuation_index_list[random.randint(0, len(current_node_continuation_index_list) -1)]]
                                                                    # by sorting within current node list of continuations
                                                                    # as there may have several occurrences of the same note,
                                                                    # this implements the probabilities of a Markov model
                    note_sequence.append(next_note) # Add this continuation note to the list of input notes
                    self.continuation_sequence.append(next_note)    # Add this continuation note to the list of continuations
                    last_input_note = next_note                     # And continue the generation from this (new) last note
        return self.continuation_sequence

    @staticmethod
    def play_midi_note(port_name, note):
        with open_output(port_name) as output:
            output.send(mido.Message('note_on', note = note.pitch, velocity = note.velocity))
            # print('play_midi_note_sequence: note.duration: ' + str(note.duration))
            time.sleep(note.duration)
            output.send(mido.Message('note_off', note = note.pitch, velocity = note.velocity))

    def listen_and_continue(self, input_port, output_port):
        with open_input(input_port) as in_port, open_output(output_port) as dummy:
            print('Currently listening on ' + str(input_port))
            self.continuation_sequence = []
            self.current_note_on_dict = {}
            self.last_note_end_time = time.time()
            while True:                                             # Infinite listening loop
                for event in in_port.iter_pending():
                    if event.type == 'note_on' and event.velocity > 0:
                        self.continuation_sequence = []
                        note = Note(event.note, None, event.velocity)
                        if note.pitch in self.current_note_on_dict:
                            print('Warning: Note ' + str(note.pitch) + ' has been repeated before being ended')
                        # print('note_on event: ' + str(event) + ' time.time: ' + str(time.time()) + ' self.last_note_end_time: ' + str(self.last_note_end_time))
                        current_time = time.time()
                        self.current_note_on_dict[note.pitch] = (note, current_time)
                        self.last_note_end_time = current_time
                        # print('new note: ' + str(note) + ' note.pitch: ' + str(note.pitch) + ' note.duration: ' + str(note.duration))
                        self.played_notes.append(note)
                    elif ((event.type == 'note_off') or (event.type == 'note_on' and event.velocity == 0)) and (event.note in self.current_note_on_dict):
                        current_time = time.time()
                        (note, note_start_time) = self.current_note_on_dict[event.note]
                        del self.current_note_on_dict[event.note]
                        note.duration = current_time - note_start_time
                        self.last_note_end_time = current_time
                        # print('note_off event: ' + str(event) + ' time.time: ' + str(time.time()) + ' self.last_note_end_time: ' + str(self.last_note_end_time) + ' self.current_note_on.duration: ' + str(self.current_note_on.duration))
                #   elif ((event.type == 'note_off') or (event.type == 'note_on' and event.velocity == 0)):
                #       None
                        # print('event.note: ' + str(event.note) + ' self.current_note_on_dict: ' + str(self.self.current_note_on_dict))
                # print('listen_and_continue: time.time(): ' + str(time.time()) + ' self.last_note_end_time: ' + str(self.last_note_end_time) + ' _silence_threshold: ' + str(_silence_threshold))
                silence_duration = time.time() - self.last_note_end_time
                # print('listen_and_continue: silence_duration: ' + str(silence_duration))
                if self.continuation_sequence:
                    self.play_midi_note(output_port, self.continuation_sequence.pop(0))
                elif self.played_notes and silence_duration > _silence_threshold and not self.current_note_on_dict:
                    # print('self.played_notes and silence_duration > _silence_threshold: pitch_sequence_from_note_sequence(played_notes):' + str(pitch_sequence_from_note_sequence(self.played_notes)))
                    # print('self.played_notes: ' + str(pitch_sequence_from_note_sequence(self.played_notes)))
                    self.train(self.played_notes)
                    # self.display_memory()
                    self.continuation_sequence = self.generate(self.played_notes[-_max_played_notes_considered:])
                    if not self.continuation_sequence:
                        print("Generation failed.")
                    self.played_notes = []
                # time.sleep(_after_continuation_sleep)

    def batch_test(self, pitch_sequence_list):
        for pitch_sequence in pitch_sequence_list:
            # print('Training with sequence: ' + str(pitch_sequence))
            note_sequence = create_note_sequence(pitch_sequence)
            self.train(note_sequence)
            self.display_memory()
            print('Continuation generated: ' + str(pitch_sequence_from_note_sequence(continuator.generate(note_sequence))))

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
                    # if pending_notes[msg.note] == None:
                        # print("Found 0 velocity note, skipping it")
                    #    continue
                    del self.current_note_on_dict[event.note]
                    note.duration = current_time - note_start_time
        return note_sequence

    def write_midi_file(self, midi_file_name, note_sequence):
            midi_file = mido.MidiFile()
            track = MidiTrack()
            midi_file.tracks.append(track)
            time = 0
            for note in note_sequence:
                # print('note_on time: ' + str(time))
                track.append(Message('note_on', time=time, note=note.pitch, velocity=note.velocity))
                # print('note.duration: ' + str(note.duration))
                # print('play_midi_note_sequence: note.duration: ' + str(note.duration))
                time += note.duration
                track.append(Message('note_off', time=time, note=note.pitch, velocity=note.velocity))
                # print('note_off time: ' + str(time))
            midi_file.save(midi_file_name)

    def run(self, mode):
        match mode:
            case 'RealTime':
                print('MIDI ports available: ' + str(get_input_names()))  # Display of MIDI ports
                input_port = get_input_names()[0]
                output_port = get_output_names()[0]
                self.listen_and_continue(input_port, output_port)
            case 'File':
                note_sequence = self.read_midi_file('Test.mid')
                self.train(note_sequence)
                # self.display_memory()
                self.continuation_sequence = self.generate(note_sequence[-_max_played_notes_considered:])
                # print('self.continuation_sequence: ' + str(self.continuation_sequence))
                self.write_midi_file('Continuation.mid', self.continuation_sequence)
            case 'Batch':    # Batch test
                self.batch_test([[48, 50, 52, 53], [48, 50, 50, 52], [48, 50], [50, 48], [48]])

continuator = PrefixTreeContinuator()
continuator.run('RealTime')
