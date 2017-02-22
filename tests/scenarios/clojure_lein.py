from os import environ
from autobump import config

handler = "clojure"
previous_clojure = config.clojure()


def setUp(repo):
    # CLASSPATH here is irrelevant, it will get ignored by lein-exec.
    config.set("autobump", "clojure", "./leinexec.sh")


def tearDown(repo):
    config.set("autobump", "clojure", previous_clojure)


commit_history = [
    ("Initial commit",
     "1.0.0",
     """
diff --git a/project.clj b/project.clj
new file mode 100644
index 0000000..cb3b805
--- /dev/null
+++ b/project.clj
@@ -0,0 +1,4 @@
+(defproject clojure_lein "0.1.0-SNAPSHOT"
+  :dependencies [[org.clojure/clojure "1.8.0"]
+                 [org.clojure/core.typed "0.3.21"]]
+  :plugins [[lein-exec "0.3.6"]])
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
new file mode 100644
index 0000000..09b5547
--- /dev/null
+++ b/src/clojure_lein/core.clj
@@ -0,0 +1,2 @@
+(ns clojure-lein.core
+  (:require [clojure.core.typed :as t]))
--
diff --git a/leinexec.sh b/leinexec.sh
new file mode 100755
index 0000000..6c722bf
--- /dev/null
+++ b/leinexec.sh
@@ -0,0 +1,2 @@
+#!/bin/bash
+{lein_executable} deps && {lein_executable} exec -p $@
     """.format(lein_executable="/home/travis/lein" if "TRAVIS" in environ else "lein")),

    ("Add public function",
     "1.1.0",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 09b5547..3225696 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -1,2 +1,5 @@
 (ns clojure-lein.core
   (:require [clojure.core.typed :as t]))
+
+(defn add [x y]
+  (+ x y))
     """),

    ("Add private function",
     "1.1.1",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 3225696..67b7af3 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -3,3 +3,5 @@

 (defn add [x y]
   (+ x y))
+
+(defn- identity [x] x)
     """),

    ("Add signature to public function",
     "1.2.0",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 67b7af3..3e377b5 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -1,7 +1,10 @@
 (ns clojure-lein.core
   (:require [clojure.core.typed :as t]))

-(defn add [x y]
-  (+ x y))
+(defn add
+  ([x y]
+   (+ x y))
+  ([x y z]
+   (+ x y z)))

 (defn- identity [x] x)
     """),

    ("Remove signature from public function",
     "2.0.0",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 3e377b5..eeebe04 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -2,9 +2,7 @@
   (:require [clojure.core.typed :as t]))

 (defn add
-  ([x y]
-   (+ x y))
-  ([x y z]
-   (+ x y z)))
+  [x y z]
+   (+ x y z))

 (defn- identity [x] x)
     """),

    ("Rename parameters",
     "2.0.1",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index eeebe04..7c80c43 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -2,7 +2,7 @@
   (:require [clojure.core.typed :as t]))

 (defn add
-  [x y z]
-   (+ x y z))
+  [a b c]
+   (+ a b c))

 (defn- identity [x] x)
     """),

    ("Type hinting",
     "3.0.0",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 7c80c43..62ccb58 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -2,7 +2,7 @@
   (:require [clojure.core.typed :as t]))

 (defn add
-  [a b c]
+  [^Integer a ^Integer b ^Integer c]
    (+ a b c))

 (defn- identity [x] x)
     """),

    ("Remove type hints",
     "3.0.1",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 62ccb58..7c80c43 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -2,7 +2,7 @@
   (:require [clojure.core.typed :as t]))

 (defn add
-  [^Integer a ^Integer b ^Integer c]
+  [a b c]
    (+ a b c))

 (defn- identity [x] x)
     """),

    ("Add function with typehinted parameter",
     "3.1.0",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 7c80c43..71902a2 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -5,4 +5,6 @@
   [a b c]
    (+ a b c))

+(defn p [^String s] (println s))
+
 (defn- identity [x] x)
     """),

    ("Relax type hint",
     "3.1.1",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 71902a2..7a973c8 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -5,6 +5,6 @@
   [a b c]
    (+ a b c))

-(defn p [^String s] (println s))
+(defn p [^Object s] (println s))

 (defn- identity [x] x)
     """),

    ("Add statically typed function",
     "3.2.0",
     """
diff --git a/project.clj b/project.clj
index f30bea7..43375ef 100644
--- a/project.clj
+++ b/project.clj
@@ -1,4 +1,4 @@
 (defproject clojure_lein "0.1.0-SNAPSHOT"
   :dependencies [[org.clojure/clojure "1.8.0"]
-                 [org.clojure/core.typed "0.3.21"]]
+                 [org.clojure/core.typed "0.3.32"]]
   :plugins [[lein-exec "0.3.6"]])
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index 7a973c8..ea9e81b 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -8,3 +8,8 @@
 (defn p [^Object s] (println s))

 (defn- identity [x] x)
+
+(t/ann sum [t/AnyInteger t/AnyInteger :-> t/AnyInteger])
+(defn sum [a b]
+  (+ a b))
+
     """),

    ("Change type annotation",
     "4.0.0",
     """
diff --git a/src/clojure_lein/core.clj b/src/clojure_lein/core.clj
index ea9e81b..6912cfb 100644
--- a/src/clojure_lein/core.clj
+++ b/src/clojure_lein/core.clj
@@ -9,7 +9,7 @@

 (defn- identity [x] x)

-(t/ann sum [t/AnyInteger t/AnyInteger :-> t/AnyInteger])
+(t/ann sum [t/Bool t/Bool :-> t/Bool])
 (defn sum [a b]
-  (+ a b))
+  (or a b))

     """)

]
