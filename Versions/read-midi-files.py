def extract_notes(self, midi_file):
        """Extracts the sequence of note-on events from a MIDI file."""
        mid = mido.MidiFile(midi_file)
        notes = []
        pending_notes = np.empty(128, dtype=object)
        pending_start_times = np.zeros(128)
        current_time = 0
        for track in mid.tracks:
            for msg in track:
                current_time += msg.time
                if msg.type == "note_on" and msg.velocity > 0:
                    new_note = Note(msg.note, msg.velocity, 0)
                    notes.append(new_note)  # Store MIDI note number
                    pending_notes[msg.note] = new_note
                    pending_start_times[msg.note] = current_time
                    new_note.set_start_time(current_time)
                    new_note.set_duration(120)
                if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                    if pending_notes[msg.note] == None:
                        print("found 0 velocity note, skipping it")
                        continue
                    pending_note = pending_notes[msg.note]
                    duration = current_time - pending_start_times[msg.note]
                    pending_note.set_duration(duration)
                    pending_notes[msg.note] = None
                    pending_start_times[msg.note] = 0
        return np.array(notes)
        