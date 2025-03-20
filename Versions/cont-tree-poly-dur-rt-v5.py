#!/usr/bin/python
# -*- coding: latin-1 -*-

import mido
import time
import random
from mido import open_input, open_output, get_input_names, get_output_names

class PrefixTreeNode:
    """Représente un n½ud dans l'arbre préfixé (stocke des accords triés)."""
    def __init__(self):
        self.children = {}
        self.continuations = []

class PrefixTreeContinuatorRealtime:
    """Continuateur polyphonique en temps réel basé sur un arbre préfixé."""
    def __init__(self, silence_threshold=2.0, duration_mode="learned"):
        self.root = PrefixTreeNode()
        self.sequences = []
        self.durations = []
        self.last_note_time = time.time()
        self.recorded_notes = []
        self.active_notes = set()  
        self.last_chord = None  
        self.silence_threshold = silence_threshold
        self.duration_mode = duration_mode  

        # ?? Séquence d?amorçage pour éviter un arbre vide au départ
        self.train([((60,), 0.3), ((64,), 0.4), ((67,), 0.5)])  

    def train(self, sequence):
        """Ajoute une séquence à l'arbre préfixé et affiche la mémoire."""
        seq_index = len(self.sequences)
        chords = [tuple(sorted(note[0])) for note in sequence]  
        durations = [note[1] for note in sequence]

        self.sequences.append(chords)
        self.durations.append(durations)

        for start in range(len(chords)):
            current_node = self.root
            for i in range(len(chords) - 1, start - 1, -1):
                chord = chords[i]
                if chord not in current_node.children:
                    current_node.children[chord] = PrefixTreeNode()
                current_node = current_node.children[chord]

                if seq_index not in current_node.continuations:
                    current_node.continuations.append(seq_index)

        print(f"? Arbre mis à jour : {len(self.sequences)} séquences enregistrées.")
        self.display_memory()  # Affichage de l'arbre

    def display_memory(self, node=None, prefix=[]):
        """Affiche une représentation de l?arbre préfixé avec les contenus des continuations."""
        if node is None:
            node = self.root
            print("\n?? **Arbre préfixé - Mémoire des séquences enregistrées**")

        for chord, child_node in node.children.items():
            continuation_indices = child_node.continuations
            continuation_data = [self.sequences[i] for i in continuation_indices]
            print(f"{' -> '.join(map(str, prefix + [chord]))}  | Continuations: {continuation_indices} => {continuation_data}")
            self.display_memory(child_node, prefix + [chord])

    def generate(self, seed, length=10):
        """Génère une continuation polyphonique avec correction du rythme."""
        if not self.sequences:
            print("?? Aucun apprentissage disponible, génération impossible.")
            return []

        generated_chords = [tuple(sorted(note[0])) for note in seed]
        generated_durations = [note[1] for note in seed]

        for _ in range(length):
            current_node = self.root
            match_found = False
            i = len(generated_chords)

            while i > 0:
                sub_prefix = tuple(generated_chords[-i:])  
                temp_node = self.root
                match_found = True
                for chord in sub_prefix:
                    if chord in temp_node.children:
                        temp_node = temp_node.children[chord]
                    else:
                        match_found = False
                        break

                if match_found and temp_node.continuations:
                    current_node = temp_node
                    break  
                i -= 1  

            if match_found and current_node.continuations:
                seq_index = random.choice(current_node.continuations)
            else:
                print("?? Aucun préfixe exact trouvé, choix d'une séquence existante.")
                seq_index = random.randint(0, len(self.sequences) - 1)

            next_pos = len(generated_chords) % len(self.sequences[seq_index])
            next_chord = self.sequences[seq_index][next_pos]
            next_duration = self.durations[seq_index][next_pos] if self.duration_mode == "learned" else generated_durations[-1]

            generated_chords.append(next_chord)
            generated_durations.append(next_duration)

        generated_sequence = list(zip(generated_chords, generated_durations))

        print("\n?? **Continuation générée**:")
        for chord, duration in generated_sequence:
            print(f"?? {chord} (Durée: {duration:.3f}s)")

        return generated_sequence

    def play_midi_output(self, port_name, chords):
        """Joue une séquence MIDI polyphonique avec correction du rythme."""
        with open_output(port_name) as output:
            for chord, duration in chords:
                for note in chord:
                    output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(duration)
                for note in chord:
                    output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """Écoute le flux MIDI et génère une continuation après un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"?? Écoute en cours sur : {input_port}")

            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()

                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.active_notes.add(msg.note)
                        self.last_note_time = current_time  

                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if msg.note in self.active_notes:
                            self.active_notes.remove(msg.note)
                        self.last_note_time = current_time  

                    sorted_chord = tuple(sorted(self.active_notes))  
                    if sorted_chord and sorted_chord != self.last_chord:
                        duration = current_time - self.last_note_time
                        print(f"?? Accord enregistré : {sorted_chord}, durée : {duration:.3f}s")
                        self.recorded_notes.append((sorted_chord, duration))
                        self.last_chord = sorted_chord  

                silence_duration = time.time() - self.last_note_time
                if self.recorded_notes and silence_duration > self.silence_threshold:
                    print("?? Silence détecté, génération de la continuation...")
                    self.train(self.recorded_notes)  
                    seed = self.recorded_notes[-2:]  
                    generated_sequence = self.generate(seed, length=10)

                    if generated_sequence:
                        self.play_midi_output(output_port, generated_sequence)
                    else:
                        print("?? Échec de la génération, pas assez de données.")

                    self.recorded_notes = []  

                time.sleep(0.01)  

print("?? Ports MIDI disponibles :", get_input_names())
input_port = get_input_names()[0]
output_port = get_output_names()[0]

continuator = PrefixTreeContinuatorRealtime(duration_mode="learned")  
continuator.listen_and_continue(input_port, output_port)
