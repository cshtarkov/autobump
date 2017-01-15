PYTHON=python3
LINTER=flake8
JAVAC=javac
AUTOBUMP_ENV=AB_ERROR_ON_EXTERNAL_TYPES=0

JAVA_FILES=$(wildcard autobump/libexec/*.java)
JAVA_CLASS_FILES=$(JAVA_FILES:.java=.class)

default: all

all: libexec lint test

# Fail if there any TODOs left in the source code.
.PHONY: todos
todos:
	! find . -name "*.py" -print | xargs grep -e "# TODO"

.PHONY: lint
lint:
	find . -name "*.py" -print | xargs $(LINTER)

.PHONY: libexec
libexec: java

.PHONY: java
java: $(JAVA_CLASS_FILES)

autobump/libexec/%.class: autobump/libexec/%.java
	$(JAVAC) $<

.PHONY: test
test: unit_test acceptance_test

.PHONY: unit_test
unit_test:
	$(PYTHON) -m unittest discover tests/

.PHONY: acceptance_test
acceptance_test:
	$(AUTOBUMP_ENV) PYTHONPATH=.: $(PYTHON) tests/scenarios/run_scenarios.py

.PHONY: clean
clean:
	rm -f autobump/libexec/*.class
