#!/usr/bin/python
# -*- coding: latin-1 -*-

import mido
import time
import random
from collections import defaultdict
from mido import open_input, open_output, get_input_names, get_output_names

#_note_default_duration = 250
_max_generated_notes = 10

class PrefixTreeNode:
    """Représente un n½ud dans l'arbre préfixé (stocke uniquement les hauteurs de notes)."""
    def __init__(self):
        self.children = {}
        self.continuations = []  # Stocke les indices des séquences apprises

class PrefixTreeContinuatorRealtime:
    """Continuateur en temps réel basé sur un arbre préfixé, avec gestion avancée des durées."""
    def __init__(self, silence_threshold=2.0, duration_mode="learned"):
        """
        silence_threshold : Temps avant que la continuation soit déclenchée (en secondes).
        duration_mode : "learned" pour utiliser les durées apprises, "input" pour reprendre les durées jouées.
        """
        self.root = PrefixTreeNode()
        self.sequences = []  # Stocke uniquement les hauteurs des séquences apprises
        self.durations = []  # Stocke les durées associées aux séquences apprises
        self.last_note_time = time.time()
        self.recorded_notes = []  # Stocke (hauteur, durée)
        self.silence_threshold = silence_threshold
        self.duration_mode = duration_mode  # Mode de gestion des durées

    def train(self, sequence):
        """Ajoute une séquence à l'arbre préfixé en ignorant les durées pour la structure."""
        seq_index = len(self.sequences)
        heights = [note[0] for note in sequence]  # Extraire uniquement les hauteurs
        durations = [note[1] for note in sequence]  # Extraire uniquement les durées

        self.sequences.append(heights)
        self.durations.append(durations)

        # Ajout dans l'arbre préfixé
        for start in range(len(heights)):
            current_node = self.root
            for i in range(len(heights) - 1, start - 1, -1):
                note = heights[i]

                if note not in current_node.children:
                    current_node.children[note] = PrefixTreeNode()

                current_node = current_node.children[note]

                if seq_index not in current_node.continuations:
                    current_node.continuations.append(seq_index)
        print("Noeuds enregistrés dans l'arbre :", len(self.sequences))

    def generate(self, seed, length=_max_generated_notes):
        """Génère une continuation à partir des hauteurs, puis réattribue les durées."""
        generated = list(seed)
        generated_heights = [note[0] for note in seed]
        print('seed: ' + str(seed))

        for p in range(length):
            print('generate: for: p: ' + str(p))
            current_node = self.root
            print('generate: current_node (= self.root): ' + str(current_node) + ' current_node.continuations: ' + str(current_node.continuations))
            match_found = False
            for i in range(len(generated_heights) - 1, -1, -1):
                print('generate: for: for: i: ' + str(i))
                note = generated_heights[i]
                print('generate: note: ' + str(note))
                print('generate: current_node.children: ' + str(current_node.children))
                if note in current_node.children:
                    current_node = current_node.children[note]
                    match_found = True
                else:
                    break

            print('generate: current_node.continuations: ' + str(current_node.continuations))
            
            if match_found and len(current_node.continuations) != 0:
                print('generate: match_found and current_node.continuations: ' + str(match_found and current_node.continuations))
                seq_index = random.choice(current_node.continuations)
                pos = len(generated_heights) % len(self.sequences[seq_index])
                next_note = self.sequences[seq_index][pos]
                print('generate: seq_index: ' + str(seq_index) + ' pos = len(generated_heights): ' + str(len(generated_heights)) + ' next_note = self.sequences[seq_index][pos]: ' + str(self.sequences[seq_index][pos]))
                generated_heights.append(next_note)
            else:
                print("Aucune continuation trouvée, choix d'une note aléatoire.")
                seq_index = random.randint(0, len(self.sequences) - 1)  # Choisir une séquence existante
#              break  # Arrêt si aucune continuation trouvée

        print('generate: generated_heights: ' + str(generated_heights))
        # Réassigner les durées
        generated_notes = []
        for i, note in enumerate(generated_heights):
            if self.duration_mode == "learned":
                # Reprendre les durées apprises
                print('generate: for: i: ' + str(i) + ' if: self.duration_mode: ' + str(self.duration_mode) + ' current_node.continuations: ' + str(current_node.continuations))
                seq_index = random.choice(current_node.continuations)
                duration = self.durations[seq_index][i % len(self.durations[seq_index])]
            else:
                print('generate: Utiliser les durées des dernières notes jouées')
                # Utiliser les durées des dernières notes jouées
                duration = seed[i % len(seed)][1] if i < len(seed) else 0.3

            print('generate: generated_notes: ' + str(generated_notes))
            generated_notes.append((note, duration))

        return generated_notes

    def play_midi_output(self, port_name, notes):
        """Joue une séquence MIDI en respectant les durées générées."""
        with open_output(port_name) as output:
            for note, duration in notes:
                output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(duration)
                output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """Écoute le flux MIDI et génère une continuation après un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"Écoute en cours sur : {input_port}")

            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()
                    if msg.type == 'note_on' and msg.velocity > 0:
                        duration = current_time - self.last_note_time
                        self.recorded_notes.append((msg.note, duration))
                        self.last_note_time = current_time

                    elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
                        self.last_note_time = current_time

                # Détection du silence et génération d'une continuation
                if self.recorded_notes and (time.time() - self.last_note_time > self.silence_threshold):
                    print("Silence détecté, génération de la continuation...")
                    self.train(self.recorded_notes)  # Apprentissage en direct
                    seed = self.recorded_notes[-2:]  # Prendre les 2 dernières notes comme seed
                    print('listen_and_continue: seed: ' + str(seed))
                    generated_sequence = self.generate(seed, length=_max_generated_notes)
                    print('listen_and_continue: generated_sequence: ' + str(generated_sequence))
                    self.play_midi_output(output_port, generated_sequence)
                    self.recorded_notes = []  # Réinitialisation

                time.sleep(0.01)  # Évite de monopoliser le CPU

# Liste des ports MIDI disponibles
print("Ports MIDI disponibles :", get_input_names())

# Sélection automatique des ports MIDI
input_port = get_input_names()[0]
output_port = get_output_names()[0]

# Lancement du continuateur en temps réel avec gestion avancée des durées
continuator = PrefixTreeContinuatorRealtime(duration_mode="learned")  # "input" pour reprendre les durées jouées
continuator.listen_and_continue(input_port, output_port)
