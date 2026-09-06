# claude-memory-hooks
.PHONY: all test gate mutate gates

all: test gate mutate gates

test:
	python engine/tests/test_memory.py

gate:
	python engine/tests/golden_recall.py

mutate:
	python engine/tests/golden_recall.py --mutate

gates:
	python method/gates/tests/test_gates.py
