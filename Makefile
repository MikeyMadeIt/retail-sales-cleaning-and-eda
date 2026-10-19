PY ?= python3

.PHONY: all test clean-outputs
all:
	$(PY) -m src.pipeline

test:
	$(PY) -m unittest discover -s tests -v

clean-outputs:
	rm -f data/clean/* output/* reports/*
