continuator = PrefixTreeContinuator()

# Test

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

time.sleep(2)

sequence_4 = [(50, 0.5), (48, 0.5)]
print("Training with sequence_4 : D, C (50, 48)")
continuator.train(sequence_4)
continuator.display_memory()

print("Generation for sequence_4")
continuation_4 = continuator.generate(sequence_4)
print("Continuation generated: ", continuation_4)

time.sleep(2)

sequence_5 = [(48, 0.5)]
print("Training with sequence_5 : C (48)")
continuator.train(sequence_4)
continuator.display_memory()

print("Generation for sequence_5")
continuation_5 = continuator.generate(sequence_5)
print("Continuation generated: ", continuation_5)
