PYTHON=python3
PIP=pip3
LINTER=flake8
JAVAC=javac
COVERAGE=coverage3
UNIT_TEST_COV_FILE=.coverage.unit
ACCEPTANCE_TEST_COV_FILE=.coverage.acceptance
AUTOBUMP_ENV=AB_ERROR_ON_EXTERNAL_TYPES=0

JAVA_FILES=$(wildcard autobump/libexec/*.java)
JAVA_CLASS_FILES=$(JAVA_FILES:.java=.class)

default: all

all: lint .coverage

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

.coverage: $(UNIT_TEST_COV_FILE) $(ACCEPTANCE_TEST_COV_FILE)
	$(COVERAGE) combine $(UNIT_TEST_COV_FILE) $(ACCEPTANCE_TEST_COV_FILE)

.PHONY: unit_test
unit_test:
	$(PYTHON) -m unittest discover tests/

$(UNIT_TEST_COV_FILE):
	COVERAGE_FILE=$(UNIT_TEST_COV_FILE) $(COVERAGE) run --branch -m unittest discover tests/

.PHONY: acceptance_test
acceptance_test:
	$(AUTOBUMP_ENV) PYTHONPATH=.: $(PYTHON) tests/scenarios/run_scenarios.py

$(ACCEPTANCE_TEST_COV_FILE):
	COVERAGE_FILE=$(ACCEPTANCE_TEST_COV_FILE) $(AUTOBUMP_ENV) PYTHONPATH=.: $(COVERAGE) run --branch tests/scenarios/run_scenarios.py

.PHONY: dist
dist:
	rm -f autobump/libexec/*.class
	$(PYTHON) setup.py sdist

.PHONY: install
install: dist
	$(PIP) install dist/autobump*.tar.gz --upgrade

.PHONY: clean
clean:
	rm -f autobump/libexec/*.class
	rm -f $(UNIT_TEST_COV_FILE) $(ACCEPTANCE_TEST_COV_FILE)
	$(COVERAGE) erase
	rm -rf dist
