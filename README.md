# autobump

[![Build Status](https://travis-ci.org/cshtarkov/autobump.svg?branch=master)](https://travis-ci.org/cshtarkov/autobump) [![codecov](https://codecov.io/gh/cshtarkov/autobump/branch/master/graph/badge.svg)](https://codecov.io/gh/cshtarkov/autobump)

**Autobump** is a Python 3 command-line tool that automatically
determines what the next version of your project should be according
to [semantic versioning](http://semver.org). 

It does so by inspecting how the public API of your software has
changed, and based on that makes a decision whether it's appropriate
to bump the major, minor or patch number. It can also generate a 
changelog.

At the moment, Autobump has support for Python, Java and Clojure
projects. It is highly modular in nature, and can be extended to
support other languages as well.

Although Autobump will work with any project that has a public API,
it is probably most useful with libraries.

## Example usage

```
$ git tag | tail -n1 # Find out the last released version.

v1.0.0

$ git diff v1.0.0 HEAD # See what has changed since then.

--- a/calculator.py
+++ b/calculator.py
@@ -1,3 +1,6 @@
 def add(a, b):
     return a+b
 
+def substract(a, b):
+    return a-b
+

$ # A subtraction function was added! This should count as a feature addition.

$ autobump python

1.1.0

$ # It does, so it bumped the minor version number. Can we see a list of changes?

$ autobump python --changelog-stdout

codebase.a.subtract: Entity was introduced
1.1.0

$
```

## How does it identify changes to the API?

The process happens in two steps. First, a language handler (see
`autobump/handlers/`) extracts the public API from the codebase and
converts it to Autobump's internal representation. This is done
twice - once for the snapshot of the last version, and once for the
current state of the project. Then some logic (see `autobump/diff.py`)
runs to determine what the changes are between the two variants.

Handlers can implement different techniques of extracting the API. For
example, the `python` and `clojure` handlers read source files and work
with the abstract syntax tree, whereas the `java_native` handler
compiles the whole project and does reflection on the resulting class files.

## License

Autobump is being developed as part of my Honours dissertation for a
BSc Hons Software Engineering at the University of Glasgow. 

The source code itself is licensed under the GNU General Public
License 3.
