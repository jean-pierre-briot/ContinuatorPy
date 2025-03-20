#!/usr/bin/python
# -*- coding: latin-1 -*-

import os
import mido
import random
from collections import defaultdict

class MarkovContinuator:
    def __init__(self, order=2):
        self.order = order
        self.markov_chain = defaultdict(list)

    def train(self, notes):
        """ Entraîne le modèle en enregistrant les transitions des notes """
        for i in range(len(notes) - self.order):
            prefix = tuple(notes[i:i + self.order])
            next_note = notes[i + self.order]
            self.markov_chain[prefix].append(next_note)

    def generate(self, seed, length=50):
        """ Génère une séquence de notes à partir d'un préfixe donné """
        if len(seed) < self.order:
            raise ValueError("Le seed doit contenir au moins {} notes".format(self.order))
        
        output = list(seed)
        for _ in range(length):
            prefix = tuple(output[-self.order:])
            print('prefix: ' + str(prefix))
            print('self.markov_chain: ' + str(self.markov_chain))
            if prefix in self.markov_chain:
                next_note = random.choice(self.markov_chain[prefix])
                output.append(next_note)
                print('appended: ' + str(next_note))
            else:
                print('break')
                break  # Arrêt si aucune transition connue
        
        print('output: ' + str(output))
        return output

    def save_to_midi(self, sequence, output_file="generated.mid", tempo=500000):
        """Sauvegarde la séquence générée dans un fichier MIDI avec durées."""
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage('set_tempo', tempo=tempo))

        for note in sequence:
            track.append(mido.Message('note_on', note=note, velocity=64, time=0))
            track.append(mido.Message('note_off', note=note, velocity=64, time=480))  # Durée variable

        mid.save(output_file)
        print(f"Fichier MIDI sauvegardé sous : {output_file}")

# Fonction pour extraire les notes d'un fichier MIDI
def extract_notes_from_midi(file_path):
    mid = mido.MidiFile(file_path)
    notes = []
    for msg in mid.tracks[0]:  # On prend seulement la première piste
        if msg.type == 'note_on' and msg.velocity > 0:
            notes.append(msg.note)
    return notes

# Exemple d'utilisation
continuator = MarkovContinuator(order=1)
seed_length=1
print('seed_length: ' + str(seed_length))
generation_length=100
print('generation_length: ' + str(generation_length))
notes = extract_notes_from_midi("input.mid")  # Charger un fichier MIDI
print('notes: ' + str(notes))
continuator.train(notes)
print('notes[:seed_length]: ' + str(notes[:seed_length]))
generated_sequence = continuator.generate(seed=notes[:seed_length], length=generation_length)
print('generated_sequence: ' + str(generated_sequence))
continuator.save_to_midi(generated_sequence, "continuation.mid")