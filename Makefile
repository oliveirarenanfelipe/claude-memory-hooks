# claude-memory-hooks
.PHONY: test gate mutate all

all: test gate mutate

test:
	python tests/test_memory.py

gate:
	python tests/golden_recall.py

mutate:
	python tests/golden_recall.py --mutate
