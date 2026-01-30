# from packaging.tags import PythonVersion

# !/usr/bin/python
# -*- coding: Unicode -*-

# Chordify (find chords from collection of notes) in Python
# Version 1.1.2
# Versions/dates: current: 29/01/2026; first: 27/12/2025
# Jean-Pierre Briot

# Mini (simplified) Chordify routine

class Pitch_Class:
    def __init__(self, name, sharp, flat):
        self.name = name
        self.sharp = sharp
        self.flat = flat

    def sharp(self):
        return self.sharp

    def flat(self):
        return self.flat

    def __repr__(self):
        #return str(self.__class__.__name__) + '(' + str(self.name) + ')'
        return str('PC') + '(' + str(self.name) + ')'

    #@classmethod
    #def repr(cls):
    #    return cls.__name__

class Pitch_Class_Natural(Pitch_Class):
    pass

class Pitch_Class_Sharp(Pitch_Class):
    pass

class Pitch_Class_Flat(Pitch_Class):
    pass

_pitch_class_A = Pitch_Class_Natural(name='A', sharp=None, flat=None)
_pitch_class_B = Pitch_Class_Natural(name='B', sharp=None, flat=None)
_pitch_class_C = Pitch_Class_Natural(name='C', sharp=None, flat=_pitch_class_B)
_pitch_class_D = Pitch_Class_Natural(name='D', sharp=None, flat=None)
_pitch_class_E = Pitch_Class_Natural(name='E', sharp=None, flat=None)
_pitch_class_F = Pitch_Class_Natural(name='F', sharp=None, flat=_pitch_class_E)
_pitch_class_G = Pitch_Class_Natural(name='G', sharp=None, flat=None)

_pitch_class_A_flat = Pitch_Class_Flat(name='Ab', sharp=_pitch_class_A, flat=_pitch_class_G)
_pitch_class_B_flat = Pitch_Class_Flat(name='Bb', sharp=_pitch_class_B, flat=_pitch_class_A)
_pitch_class_D_flat = Pitch_Class_Flat(name='Db', sharp=_pitch_class_D, flat=_pitch_class_C)
_pitch_class_E_flat = Pitch_Class_Flat(name='Eb', sharp=_pitch_class_E, flat=_pitch_class_D)
_pitch_class_G_flat = Pitch_Class_Flat(name='Gb', sharp=_pitch_class_G, flat=_pitch_class_F)


_pitch_class_A.sharp = _pitch_class_B_flat
_pitch_class_A.flat  = _pitch_class_A_flat
_pitch_class_B.sharp = _pitch_class_C
_pitch_class_B.flat  = _pitch_class_B_flat
_pitch_class_C.sharp = _pitch_class_D_flat
_pitch_class_D.flat  = _pitch_class_D_flat
_pitch_class_D.sharp = _pitch_class_E_flat
_pitch_class_E.flat  = _pitch_class_E_flat
_pitch_class_E.sharp = _pitch_class_F
_pitch_class_F.sharp = _pitch_class_G_flat
_pitch_class_G.flat  = _pitch_class_G_flat
_pitch_class_G.sharp = _pitch_class_A_flat

class Notes_Interval:
    def __init__(self, low, high):
        self.low = low
        self.high = high

class Unison(Notes_Interval):
    pass

class Minor_Second(Notes_Interval):
    pass

class Major_Second(Notes_Interval):
    pass

class Third(Notes_Interval):
    pass

class Minor_Third(Third):
    pass

class Major_Third(Third):
    pass

class Perfect_Fourth(Notes_Interval):
    pass

class Fifth(Notes_Interval):
    pass

class Diminished_Fifth(Fifth):
    pass

class Perfect_Fifth(Fifth):
    pass

class Augmented_Fifth(Fifth):
    pass

class Major_Sixth(Notes_Interval):
    pass

class Seventh(Notes_Interval):
    pass

class Minor_Seventh(Seventh):
    pass

class Major_Seventh(Seventh):
    pass

_midi_pitch_pitch_class_dictionary =    {0: _pitch_class_C,
                                         1: _pitch_class_D_flat,
                                         2: _pitch_class_D,
                                         3: _pitch_class_E_flat,
                                         4: _pitch_class_E,
                                         5: _pitch_class_F,
                                         6: _pitch_class_G,
                                         7: _pitch_class_A_flat,
                                         8: _pitch_class_A,
                                         9: _pitch_class_B_flat,
                                        10: _pitch_class_B,
                                        11: _pitch_class_C}

_pitch_delta_interval_dictionary =      {0: Unison,
                                         1: Minor_Second,
                                         2: Major_Second,
                                         3: Minor_Third,
                                         4: Major_Third,
                                         5: Perfect_Fourth,
                                         6: Diminished_Fifth,
                                         7: Perfect_Fifth,
                                         8: Augmented_Fifth,
                                         9: Major_Sixth,
                                        10: Minor_Seventh,
                                        11: Major_Seventh}

_pitch_delta_chord_interval_dictionary = {0: '(8)',
                                         1: '(b9)',
                                         2: '(9)',
                                         3: '(#9)',
                                         4: '(b11)',
                                         5: '(11)',
                                         6: '(#11)',
                                         8: '(b13)',
                                         9: '(13)',
                                        10:'(#13)'}

class Chord:
    def __init__(self, root):
        self.root = root

    def __repr__(self):
        return str(self.root) + str(self.__class__.__name__)

    @classmethod
    def repr(cls):
        return cls.__name__

class Minor_Chord(Chord):
    pass

class Major_Chord(Chord):
    pass

class Minor_Diminished(Chord):
    pass

class Augmented_Chord(Chord):
    pass

class Minor_Minor_Seventh_Chord(Chord):
    pass

class Minor_Major_Seventh_Chord(Chord):
    pass

class Major_Minor_Seventh_Chord(Chord):
    pass

class Major_Major_Seventh_Chord(Chord):
    pass

class Augmented_Fifth_Major_Seventh_Chord(Chord):
    pass

class Augmented_Minor_Seventh_Chord(Chord):
    pass

class Diminished_Chord(Chord):
    pass

class Semi_Diminished_Chord(Chord):
    pass

class Unknown_Chord(Chord):
    pass

class PNote:                                 # Structure of a note
    def __init__(self, pitch):
        self.pitch = pitch

    def match(self, note):      # Check if current note characteristics (pitch, duration and velocity) is matching some other note (only pitch)
        return note.pitch == self.pitch

    def __repr__(self):
        #return str(self.pitch_class()) + str((self.pitch)//12)
        return str(self.pitch_class())

    def pitch(self):
        return self.pitch

    def pitch_class(self):
        return _midi_pitch_pitch_class_dictionary[self.pitch%12]

    def one_octave_down(self):
        return PNote(self.pitch - 12)

    def interval(self, high):
        return _pitch_delta_interval_dictionary[(high.pitch - self.pitch)%12](self.pitch, high.pitch)

def pnote_sequence_to_pitch_sequence(pnote_sequence):
    pitch_sequence = []
    for pnote in pnote_sequence:
        pitch_sequence.append(pnote.pitch)
    return pitch_sequence

def pitch_sequence_to_pnote_sequence(pitch_sequence):        # For Batch test
    pnote_sequence = []
    for pitch in pitch_sequence:
        pnote = PNote(pitch)
        pnote_sequence.append(pnote)
    return pnote_sequence

_c4 = PNote(60)
_db4 = PNote(61)
_d4 = PNote(62)
_eb4 = PNote(63)
_e4 = PNote(64)
_f4 = PNote(65)
_gb4 = PNote(66)
_g4 = PNote(67)
_ab4 = PNote(68)
_a4 = PNote(69)
_bb4 = PNote(70)
_b4 = PNote(71)

_c5 = PNote(60 + 12)
_db5 = PNote(61 + 12)
_d5 = PNote(62 + 12)
_eb5 = PNote(63 + 12)
_e5 = PNote(64 + 12)
_f5 = PNote(65 + 12)
_gb5 = PNote(66 + 12)
_g5 = PNote(67 + 12)
_ab5 = PNote(68 + 12)
_a5 = PNote(69 + 12)
_bb5 = PNote(70 + 12)
_b5 = PNote(71 + 12)

_f6 = PNote(65 + 24)
_ab7 = PNote(68 + 36)

def chordify_pitch_list(pitch_ordered_list):
    return chordify(pitch_sequence_to_pnote_sequence(pitch_ordered_list))

def chordify(note_ordered_list):
    match len(note_ordered_list):
        case [0, 1, 2]:
            raise RuntimeError('A chord has least 3 notes and this list has only ' + str(len(note_ordered_list)))
        case 3:
            is_triad = True
            third_interval = None
        case _:
            is_triad = False
    current_note_ordered_list = note_ordered_list
    _is_stack_of_thirds_found = False
    number_of_remaining_inversions = len(note_ordered_list)
    while number_of_remaining_inversions > 0:
        first_interval = current_note_ordered_list[0].interval(current_note_ordered_list[1])
        if isinstance(first_interval, Third):       # or isinstance(first_interval, Perfect_Fourth):
            second_interval = current_note_ordered_list[1].interval(current_note_ordered_list[2])
            if isinstance(second_interval, Third):
                if is_triad:
                    _is_stack_of_thirds_found = True
                    break
                else:
                    third_interval = current_note_ordered_list[2].interval(current_note_ordered_list[3])
                    if isinstance(third_interval, Third):
                        _is_stack_of_thirds_found = True
                        break
        highest_note = current_note_ordered_list[-1]
        lowest_note = current_note_ordered_list[0]
        while highest_note.pitch >= lowest_note.pitch:
            highest_note = highest_note.one_octave_down()
        current_note_ordered_list = [highest_note] + current_note_ordered_list[:-1]
        number_of_remaining_inversions -= 1
    if _is_stack_of_thirds_found:
        if is_triad:
            index_extended_note_list = 3
        else:
            index_extended_note_list = 4
        return chord_from_intervals(first_interval, second_interval, third_interval), interval_list_from_note_list(first_interval.low, current_note_ordered_list[index_extended_note_list:])
    else:
        print('Warning: Cannot name a chord corresponding to the following notes: ' + str(note_ordered_list))
        return Unknown_Chord(PNote(first_interval.low)), []

def chord_from_intervals(first_interval, second_interval, third_interval):
    root = first_interval.low
    class_first_interval = type(first_interval)
    class_second_interval = type(second_interval)
    if not third_interval:
        if class_first_interval == Major_Third:
            if class_second_interval == Major_Third:
                return Augmented_Chord(PNote(root))
            elif class_second_interval == Minor_Third:
                return Major_Chord(PNote(root))
            else:
                return Chord(PNote(root))
        elif class_first_interval == Minor_Third:
            if class_second_interval == Major_Third:
                return Minor_Chord(PNote(root))
            elif class_second_interval == Minor_Third:
                return Minor_Diminished(PNote(root))
            else:
                return Chord(PNote(root))
    else:
        class_third_interval = type(third_interval)
        if class_first_interval == Major_Third:
            if class_second_interval == Major_Third:
                if class_third_interval == Major_Third:
                    return Augmented_Chord(PNote(root))  # + Unison Octave up
                elif class_third_interval == Minor_Third:
                    return Augmented_Major_Seventh_Chord(PNote(root))
                else:
                    return Chord(PNote(root))
            elif class_second_interval == Minor_Third:
                if class_third_interval == Major_Third:
                    return Major_Major_Seventh_Chord(PNote(root))
                elif class_third_interval == Minor_Third:
                    return Major_Minor_Seventh_Chord(PNote(root))
                else:
                    return Chord(PNote(root))
            else:
                return Major_Chord(PNote(root))
        elif class_first_interval == Minor_Third:
            if class_second_interval == Major_Third:
                if class_third_interval == Major_Third:
                    return Minor_Major_Seventh_Chord(PNote(root))
                elif class_third_interval == Minor_Third:
                    return Minor_Minor_Seventh_Chord(PNote(root))
                else:
                    return Major_Chord(PNote(root))
            elif class_second_interval == Minor_Third:
                if class_third_interval == Major_Third:
                    return Semi_Diminished_Chord(PNote(root))
                elif class_third_interval == Minor_Third:
                    return Diminished_Chord(PNote(root))
                else:
                    return Chord(PNote(root))
        else:
            return Chord(PNote(root))

def interval_list_from_note_list(root, extended_note_list):
    if not extended_note_list:
        return []
    else:
        return [interval_from_notes(root, extended_note_list[0])] + interval_list_from_note_list(root, extended_note_list[1:])

def interval_from_notes(low, high):
    return _pitch_delta_chord_interval_dictionary[(high.pitch - low)%12]

#match Minor_Third(low=1, high=2), Major_Third(low=1, high=2):
#    case Major_Third(low=x, high=y), Minor_Third(low=z, high=t):
#        print('Major')
#    case Minor_Third(low=x, high=y), Major_Third(low=z, high=t):
#        print('Minor')

#match type(Minor_Third(1, 2)), type(Major_Third(1, 2)):
#    case Major_Third, Minor_Third:
#        print('Major')
#    case Minor_Third, Major_Third:
#        print('Minor')

#match Minor_Third, Major_Third:
#    case Major_Third, Minor_Third:
#        print('Major')
#    case Minor_Third, Major_Third:
#        print('Minor')

#_some_minor_third = Minor_Third(1, 4)
#_some_major_third = Major_Third(1, 5)
#print(type(_some_minor_third) == Minor_Third)
#print(type(_some_minor_third) == Major_Third)
#print(str(type(_some_minor_third)) == str(Minor_Third))
#print(str(type(_some_minor_third)) == str(Major_Third))

#match Minor_Third:
#    case Major_Third:
#        print('Major')
#    case str(Minor_Third):
#        print('Minor')
#    case _:
#        print('Other')

#match str(type(_some_minor_third)), str(type(_some_major_third)):
#    case str(Major_Third), str(Minor_Third):
#        print('Major')
#    case str(Minor_Third), str(Major_Third):
#        print('Minor')
#    case str(Minor_Third), interval if interval == str(Minor_Third):
#        print('2Minor')
#    case _:
#        print('Other')

#print('chordify([_c4, _e4, _g4]) C: ' + str(chordify([_c4, _e4, _g4])))  # C

#print('chordify([_c4, _e4, _g4]) C/E: ' + str(chordify([_e4, _g4, _c5])))  # C 1st inversion

#print('chordify([_g4, _c5, _e5]) C/G: ' + str(chordify([_g4, _c5, _e5])))  # C 2nd inversion

#print('chordify([_c4, _eb4, _g4] C-: ' + str(chordify([_c4, _eb4, _g4])))  # C-

#print('chordify([_c4, _e4, _g4, _b4] CM7: ' + str(chordify([_c4, _e4, _g4, _b4])))  # CM7

#print('chordify([_c4, _e4, _g4, _bb4] C7: ' + str(chordify([_c4, _e4, _g4, _bb4])))  # C-7

#print('chordify([_c4, _eb4, _g4, _bb4]) C-7: ' + str(chordify([_c4, _eb4, _g4, _bb4])))  # C-7

#print('chordify([_c4, _eb4, _g4, _b4]) C-M7: ' + str(chordify([_c4, _eb4, _g4, _b4])))  # CM7

#print('chordify([_c4, _eb4, _gb4, _a4]) C°: ' + str(chordify([_c4, _eb4, _gb4, _a4])))  # C°

#print('chordify([_c4, _eb4, _gb4, _bb4]): C semi-diminished: ' + str(chordify([_c4, _eb4, _gb4, _bb4])))  # C Semi-diminished

#print('chordify([_c4, _eb4, _gb4, _bb4, _d5, _ab5, _f6, _a6]]): C semi-diminished (b9)(11)(b13) : ' + str(chordify([_c4, _eb4, _gb4, _bb4, _db5, _f5, _ab5])))  # C Semi-diminished (b9)(11)(b13)

#print('chordify([_c4, _eb4, _gb4, _bb4, _d5, _ab5, _f6, _a6]]): C semi-diminished (b9)(11)(b13) : ' + str(chordify([_c4, _eb4, _gb4, _bb4, _db5, _f6, _ab7])))  # C Semi-diminished (b9)(11)(b13)

#print('chordify([_c4, _d4, _e4, _g4, _bb4]]): C7 (2) Mu-Chord : ' + str(chordify([_c4, _d4, _e4, _g4, _bb4])))  # C7 (2) Mu-Chord

#print('chordify([_c4, _f4, _g4, _bb4]]): C7sus4 : ' + str(chordify([_c4, _f4, _gb4, _bb4])))  # C7sus4
