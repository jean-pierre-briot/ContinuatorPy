#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

#hyperparameters
_silence_threshold = 2.0
_max_continuation_length = 10

class PrefixTreeNode:
    def __init__(self):
        self.note = None
        self.children_list = None
        self.continuation_list = None

class PrefixTreeContinuator:
    def __init__(self):
        self.root_dictionary = {}

    def train(self, event_sequence):
        # event_sequence = [(<pitch>, <duration>), ... , (<pitch>, <duration>)]
        note_sequence = [note for note, dummy in event_sequence]
        # note_sequence: [<pitch>, ... , <pitch>]
        # for k in range(len(note_sequence) - 1, -1 -1):		Does not work correctly ?!!
        i = len(note_sequence) - 1
        while i > 0:
            # i will vary from length-1 (pre-last element: note_n-1) to 0 (first element: note_1)
            # for k in range(len(note_sequence) - 1, -1 - 1): Does not work correctly (?)
            note_sub_sequence = note_sequence[:i]                   # Prefix Sub-sequence: [note_1, .. , note_i]
            continuation = note_sequence[i]                         # Continuation = note_i
            reversed_note_sub_sequence = note_sub_sequence[::-1]    # Reversed Sub-sequence: [note_i, ..., note_1]
            root_note = reversed_note_sub_sequence[0]               # Note of the root of the tree to be created: note_i
            if root_note not in self.root_dictionary:
                current_node = PrefixTreeNode()
                self.root_dictionary[root_note] = current_node
                current_node.note = root_note
                current_node.continuation_list = [continuation]
            else:
                current_node = self.root_dictionary[root_note]
                current_node.continuation_list.append(continuation)
            for note in reversed_note_sub_sequence[1:]:
                if current_node.children_list is None:
                    new_child_node = PrefixTreeNode()
                    new_child_node.note = note
                    new_child_node.continuation_list = [continuation]
                    current_node.children_list = [new_child_node]
                    current_node = new_child_node
                else:
                    node_exists = False
                    for child_node in current_node.children_list:
                        if child_node.note == note:
                            child_node.continuation_list.append(continuation)
                            node_exists = True
                            current_node = child_node
                            break
                    if not(node_exists):
                        new_child_node = PrefixTreeNode()
                        new_child_node.note = note
                        new_child_node.continuation_list = [continuation]
                        current_node.children_list.append(new_child_node)
                        current_node = new_child_node
            i = i - 1

    def display_memory(self):
        print("Memory:")
        for root_note, root in self.root_dictionary.items():
            self.display_tree(root, 0)

    def display_tree(self, node, level):
        indent = '  ' * level
        print(indent, end='')
        print(str(node.note) + str(node.continuation_list))
        if node.children_list != None:
            for child in node.children_list:
                self.display_tree(child, level + 1)

    def generate(self, event_sequence):
        note_sequence = [note for note, dur in event_sequence]
        last_input_note = note_sequence[-1]
        continuation_sequence = []
        for i in range(1, _max_continuation_length):
            if last_input_note not in self.root_dictionary:
                print('Last played note: ' + str(last_input_note) + ' has no matching tree root thus I cannot generate continuation')
                break
            else:
                current_node = self.root_dictionary[last_input_note]
                j = 2
                while (current_node.children_list is not None) and len(note_sequence) > j - 1:
                    matching_child = None
                    for child in current_node.children_list:
                        if child.note == note_sequence[-j]:
                            matching_child = child
                            break
                    if matching_child == None:
                        break
                    else:
                        current_node = matching_child
                        j = j + 1
                if current_node.children_list == None or len(note_sequence) < j or matching_child == None:
                    current_node_continuation_list = current_node.continuation_list
                    next_note = current_node_continuation_list[random.randint(0, len(current_node_continuation_list) - 1)]
                    note_sequence.append(next_note)
                    continuation_sequence.append(next_note)
                    last_input_note = next_note
        return continuation_sequence

# ------------------- Mode Test -------------------
if __name__ == '__main__':
    continuator = PrefixTreeContinuator()

    sequence_1 = [(48, 0.5), (50, 0.5), (52, 0.5), (53, 0.5)]
    print("Training with sequence_1: C, D, E, F (48, 50, 52, 53)")
    continuator.train(sequence_1)
    continuator.display_memory()

    continuation_1 = continuator.generate(sequence_1)
    print("Continuation generated: ", continuation_1)

    # Simulate some silence
    time.sleep(2)

    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("Training with sequence_2 : C, D, D, E (48, 50, 50, 52)")
    continuator.train(sequence2)
    continuator.display_memory()

    continuation_2 = continuator.generate(sequence2)
    print("Continuation generated: ", continuation_2)

    time.sleep(2)

    sequence_3 = [(48, 0.5), (50, 0.5)]
    print("Training with sequence_3 : C, D (48, 50)")
    continuator.train(sequence_3)
    continuator.display_memory()

    print("Generation for sequence_3")
    continuation_3 = continuator.generate(sequence_3)
    print("Continuation generated: ", continuation_3)
