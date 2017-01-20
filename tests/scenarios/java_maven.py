import os
import sys
from subprocess import Popen, PIPE

handler = "java_native"
build_command = "mvn compile"
build_root = "target/classes"

# TODO: Think of better names
def before_advice(repo):
    cmd = ["mvn", "dependency:build-classpath", "-Dmdep.outputFile=classpath.txt"]
    child = Popen(cmd,
                  cwd=repo,
                  stdout=PIPE,
                  stderr=PIPE)
    child.communicate()
    if child.returncode != 0:
        # TODO: what now?
        print("Failed to get classpath from Maven!", file=sys.stderr)
        exit(1)
    with open(os.path.join(repo, "classpath.txt")) as classpathf:
        classpath = classpathf.read()
    # If we set the classpath to exactly what Maven told us, then
    # Autobump's own utilities won't work. That's why we need to add the
    # current directory to the end as well.
    os.environ["CLASSPATH"] = classpath + ":.:"
    print("Classpath set to: {}".format(classpath), file=sys.stderr)

commit_history = [

    ("Initial commit",
     "1.0.0",
     """
diff --git a/pom.xml b/pom.xml
new file mode 100644
index 0000000..32e822a
--- /dev/null
+++ b/pom.xml
@@ -0,0 +1,9 @@
+<project xmlns="http://maven.apache.org/POM/4.0.0"
+         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
+         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
+                             http://maven.apache.org/xsd/maven-4.0.0.xsd">
+  <modelVersion>4.0.0</modelVersion>
+  <groupId>com.autobump</groupId>
+  <artifactId>mavenproject</artifactId>
+  <version>1.0.0</version>
+</project>
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
new file mode 100644
index 0000000..7b23a0c
--- /dev/null
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -0,0 +1,4 @@
+package com.autobump.somepackage;
+
+public class ClassA {
+}
--
2.11.0
     """),

    ("Add public field",
     "1.1.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 7b23a0c..ebd0510 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -1,4 +1,5 @@
 package com.autobump.somepackage;

 public class ClassA {
+    public static int somefield;
 }
--
2.11.0
     """),

    ("Add public method",
     "1.2.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index ebd0510..e334f96 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -2,4 +2,6 @@ package com.autobump.somepackage;

 public class ClassA {
     public static int somefield;
+
+    public void publicmethod() {}
 }
     """),

    ("Add private method",
     "1.2.1",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index e334f96..351bd84 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -3,5 +3,6 @@ package com.autobump.somepackage;
 public class ClassA {
     public static int somefield;

+    private void privatemethod() {}
     public void publicmethod() {}
 }
     """)

]
