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
     """),

    ("Add parameter to method",
     "2.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 351bd84..cb531e9 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -4,5 +4,5 @@ public class ClassA {
     public static int somefield;

     private void privatemethod() {}
-    public void publicmethod() {}
+    public void publicmethod(int a) {}
 }
     """),

    ("Overload method",
     "2.1.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index cb531e9..80caeee 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -5,4 +5,5 @@ public class ClassA {

     private void privatemethod() {}
     public void publicmethod(int a) {}
+    public void publicmethod(int a, int b) {}
 }
     """),

    ("Remove overloaded method",
     "3.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 80caeee..6738cc9 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -4,6 +4,5 @@ public class ClassA {
     public static int somefield;

     private void privatemethod() {}
-    public void publicmethod(int a) {}
     public void publicmethod(int a, int b) {}
 }
     """),

    ("Change method return type",
     "4.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 6738cc9..75779ef 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -4,5 +4,5 @@ public class ClassA {
     public static int somefield;

     private void privatemethod() {}
-    public void publicmethod(int a, int b) {}
+    public int publicmethod(int a, int b) {return 0;}
 }
     """),

    ("Change type of parameter",
     "5.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 75779ef..a54fa7f 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -4,5 +4,5 @@ public class ClassA {
     public static int somefield;

     private void privatemethod() {}
-    public int publicmethod(int a, int b) {return 0;}
+    public int publicmethod(String a, int b) {return 0;}
 }
     """),

    ("Add new class",
     "5.1.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassB.java b/src/main/java/com/autobump/somepackage/ClassB.java
new file mode 100644
index 0000000..d451ade
--- /dev/null
+++ b/src/main/java/com/autobump/somepackage/ClassB.java
@@ -0,0 +1,4 @@
+package com.autobump.somepackage;
+
+public class ClassB extends ClassA {
+}
     """),

    ("Add new method",
     "5.2.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index a54fa7f..4b3b119 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -5,4 +5,6 @@ public class ClassA {

     private void privatemethod() {}
     public int publicmethod(String a, int b) {return 0;}
+
+    public void m(ClassB p) {}
 }
     """),

    ("Change type of parameter to superclass",
     "5.2.1",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 4b3b119..16f37b4 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -6,5 +6,5 @@ public class ClassA {
     private void privatemethod() {}
     public int publicmethod(String a, int b) {return 0;}

-    public void m(ClassB p) {}
+    public void m(ClassA p) {}
 }
     """),

    ("Change type of parameter to subclass",
     "6.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 16f37b4..4b3b119 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -6,5 +6,5 @@ public class ClassA {
     private void privatemethod() {}
     public int publicmethod(String a, int b) {return 0;}

-    public void m(ClassA p) {}
+    public void m(ClassB p) {}
 }
     """),

    ("Add external dependency (Guava)",
     "6.1.0",
     """
diff --git a/pom.xml b/pom.xml
index 32e822a..949a126 100644
--- a/pom.xml
+++ b/pom.xml
@@ -2,6 +2,16 @@
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                              http://maven.apache.org/xsd/maven-4.0.0.xsd">
+
+  <!-- https://mvnrepository.com/artifact/com.google.guava/guava -->
+  <dependencies>
+    <dependency>
+      <groupId>com.google.guava</groupId>
+      <artifactId>guava</artifactId>
+      <version>21.0</version>
+    </dependency>
+  </dependencies>
+
   <modelVersion>4.0.0</modelVersion>
   <groupId>com.autobump</groupId>
   <artifactId>mavenproject</artifactId>
diff --git a/src/main/java/com/autobump/somepackage/ClassB.java b/src/main/java/com/autobump/somepackage/ClassB.java
index d451ade..6455580 100644
--- a/src/main/java/com/autobump/somepackage/ClassB.java
+++ b/src/main/java/com/autobump/somepackage/ClassB.java
@@ -1,4 +1,7 @@
 package com.autobump.somepackage;
+import com.google.common.collect.Multiset;
+import com.google.common.collect.ImmutableMultiset;

 public class ClassB extends ClassA {
+    public void m(ImmutableMultiset s) {}
 }
     """),

    # TODO: BUG: This test fails.
    # ClassB extends ClassA, so m() is overloaded:
    # Variant A is: void m(ClassB), void m(ImmutableMultiset)
    # Variant B is: void m(ClassB), void m(Multiset)
    ("Change type of parameter to interface",
     "6.1.1",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassB.java b/src/main/java/com/autobump/somepackage/ClassB.java
index 6455580..548a1fe 100644
--- a/src/main/java/com/autobump/somepackage/ClassB.java
+++ b/src/main/java/com/autobump/somepackage/ClassB.java
@@ -3,5 +3,5 @@ import com.google.common.collect.Multiset;
 import com.google.common.collect.ImmutableMultiset;

 public class ClassB extends ClassA {
-    public void m(ImmutableMultiset s) {}
+    public void m(Multiset s) {}
 }
     """)

]
