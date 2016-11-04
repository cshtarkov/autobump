PYTHON=python3
LINTER=flake8
JAVAC=javac

JAVA_FILES=$(wildcard autobump/libexec/*.java)
JAVA_CLASS_FILES=$(JAVA_FILES:.java=.class)

default: all

all: libexec lint test

# Fail if there any TODOs left in the source code.
todos:
	! find . -name "*.py" -print | xargs grep -e "TODO"

lint:
	find . -name "*.py" -print | xargs $(LINTER)

libexec: java

java: $(JAVA_CLASS_FILES)

autobump/libexec/%.class: autobump/libexec/%.java
	$(JAVAC) $<

test:
	$(PYTHON) -m unittest discover tests/

clean:
	rm -f autobump/libexec/*.class
