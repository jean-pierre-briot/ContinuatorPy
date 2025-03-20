import mido
import random
from collections import defaultdict

class MarkovContinuator:
    def __init__(self, order=2):
        self.order = order
        self.markov_chain = defaultdict(list)

    def train(self, notes):
        "Entraine le modele en enregistrant les transitions des notes"
        for i in range(len(notes) - self.order):
            prefix = tuple(notes[i:i + self.order])
            next_note = notes[i + self.order]
            self.markov_chain[prefix].append(next_note)

    def generate(self, seed, length=50):
        "Genere une sequence de notes a partir d'un prefixe donne"
        if len(seed) < self.order:
            raise ValueError("Le seed doit contenir au moins {} notes".format(self.order))
        
        output = list(seed)
        for _ in range(length):
            prefix = tuple(output[-self.order:])
            if prefix in self.markov_chain:
                next_note = random.choice(self.markov_chain[prefix])
                output.append(next_note)
            else:
                break  # Arret si aucune transition connue
        
        return output

    def save_to_midi(self, sequence, output_file="generated.mid", tempo=500000):
        "Sauvegarde la sequence generee dans un fichier MIDI."
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage('set_tempo', tempo=tempo))

        for note in sequence:
            track.append(mido.Message('note_on', note=note, velocity=64, time=0))
            track.append(mido.Message('note_off', note=note, velocity=64, time=480))  # Note de duree fixe

        mid.save(output_file)
        print(f"Fichier MIDI sauvegarde sous : {output_file}")
        
# Exemple d'utilisation
continuator = MarkovContinuator(order=2)
continuator.train("input.mid")
generated_sequence = continuator.generate(seed=[60, 62, 65], length=20)
print(generated_sequence)
continuator.save_to_midi(generated_sequence, "continuation.mid")

