import os
import sys

from autobump.common import popen

handler = "java_native"
build_command = "mvn compile"
build_root = "target/classes"
previous_classpath = os.environ.get("CLASSPATH", None)


def setUp(repo):
    cmd = ["mvn", "dependency:build-classpath", "-Dmdep.outputFile=classpath.txt"]
    return_code, _, _ = popen(cmd, cwd=repo)
    if return_code != 0:
        print("Failed to get classpath from Maven!", file=sys.stderr)
        exit(1)
    with open(os.path.join(repo, "classpath.txt")) as classpathf:
        classpath = classpathf.read()
    # If we set the classpath to exactly what Maven told us, then
    # Autobump's own utilities won't work. That's why we need to add the
    # current directory to the end as well.
    os.environ["CLASSPATH"] = classpath + ":.:"


def tearDown(_):
    if previous_classpath is not None:
        os.environ["CLASSPATH"] = previous_classpath


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
     """),

    ("Add new package",
     "6.2.0",
     """
diff --git a/src/main/java/com/autobump/anotherpackage/ClassC.java b/src/main/java/com/autobump/anotherpackage/ClassC.java
new file mode 100644
index 0000000..5473f84
--- /dev/null
+++ b/src/main/java/com/autobump/anotherpackage/ClassC.java
@@ -0,0 +1,4 @@
+package com.autobump.anotherpackage;
+
+public class ClassC {
+}
diff --git a/src/main/java/com/autobump/anotherpackage/InterfaceD.java b/src/main/java/com/autobump/anotherpackage/InterfaceD.java
new file mode 100644
index 0000000..b7e5412
--- /dev/null
+++ b/src/main/java/com/autobump/anotherpackage/InterfaceD.java
@@ -0,0 +1,4 @@
+package com.autobump.anotherpackage;
+
+public interface InterfaceD {
+}
     """),

    ("Implement interface",
     "6.2.1",
     """
diff --git a/src/main/java/com/autobump/anotherpackage/ClassC.java b/src/main/java/com/autobump/anotherpackage/ClassC.java
index 5473f84..54ab335 100644
--- a/src/main/java/com/autobump/anotherpackage/ClassC.java
+++ b/src/main/java/com/autobump/anotherpackage/ClassC.java
@@ -1,4 +1,4 @@
 package com.autobump.anotherpackage;

-public class ClassC {
+public class ClassC implements InterfaceD {
 }
     """),

    ("Add method with wildcard import",
     "6.3.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 4b3b119..a112e69 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -1,4 +1,5 @@
 package com.autobump.somepackage;
+import com.autobump.anotherpackage.*;

 public class ClassA {
     public static int somefield;
@@ -6,5 +7,7 @@ public class ClassA {
     private void privatemethod() {}
     public int publicmethod(String a, int b) {return 0;}

+    public void dosmth(ClassC p) {}
+
     public void m(ClassB p) {}
 }
     """),

    ("Change type of parameter to interface",
     "6.3.1",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index a112e69..7613064 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -7,7 +7,7 @@ public class ClassA {
     private void privatemethod() {}
     public int publicmethod(String a, int b) {return 0;}

-    public void dosmth(ClassC p) {}
+    public void dosmth(InterfaceD p) {}

     public void m(ClassB p) {}
 }
     """),

    ("Overload method",
     "6.4.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 7613064..576a499 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -8,6 +8,7 @@ public class ClassA {
     public int publicmethod(String a, int b) {return 0;}

     public void dosmth(InterfaceD p) {}
+    public void dosmth(ClassC p) {}

     public void m(ClassB p) {}
 }
     """),

    ("Change return type of method",
     "7.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index 576a499..fb737fe 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -8,7 +8,7 @@ public class ClassA {
     public int publicmethod(String a, int b) {return 0;}

     public void dosmth(InterfaceD p) {}
-    public void dosmth(ClassC p) {}
+    public int dosmth(ClassC p) {return 0;}

     public void m(ClassB p) {}
 }
     """),

    ("Change type of parameter to interface",
     "7.1.0",
     """
diff --git a/src/main/java/com/autobump/anotherpackage/ClassC.java b/src/main/java/com/autobump/anotherpackage/ClassC.java
index 54ab335..b524110 100644
--- a/src/main/java/com/autobump/anotherpackage/ClassC.java
+++ b/src/main/java/com/autobump/anotherpackage/ClassC.java
@@ -1,4 +1,4 @@
 package com.autobump.anotherpackage;

-public class ClassC implements InterfaceD {
+public class ClassC implements InterfaceD, InterfaceE {
 }
diff --git a/src/main/java/com/autobump/anotherpackage/InterfaceE.java b/src/main/java/com/autobump/anotherpackage/InterfaceE.java
new file mode 100644
index 0000000..f9d3d60
--- /dev/null
+++ b/src/main/java/com/autobump/anotherpackage/InterfaceE.java
@@ -0,0 +1,4 @@
+package com.autobump.anotherpackage;
+
+public interface InterfaceE {
+}
diff --git a/src/main/java/com/autobump/somepackage/ClassA.java b/src/main/java/com/autobump/somepackage/ClassA.java
index fb737fe..a6cb81b 100644
--- a/src/main/java/com/autobump/somepackage/ClassA.java
+++ b/src/main/java/com/autobump/somepackage/ClassA.java
@@ -8,7 +8,7 @@ public class ClassA {
     public int publicmethod(String a, int b) {return 0;}

     public void dosmth(InterfaceD p) {}
-    public int dosmth(ClassC p) {return 0;}
+    public int dosmth(InterfaceE p) {return 0;}

     public void m(ClassB p) {}
 }
     """),

    ("Change type of parameter to type of same name",
     "8.0.0",
     """
diff --git a/src/main/java/com/autobump/anotherpackage/Multiset.java b/src/main/java/com/autobump/anotherpackage/Multiset.java
new file mode 100644
index 0000000..a5fc7c2
--- /dev/null
+++ b/src/main/java/com/autobump/anotherpackage/Multiset.java
@@ -0,0 +1,4 @@
+package com.autobump.anotherpackage;
+
+public class Multiset {
+}
diff --git a/src/main/java/com/autobump/somepackage/ClassB.java b/src/main/java/com/autobump/somepackage/ClassB.java
index 548a1fe..a0b34dc 100644
--- a/src/main/java/com/autobump/somepackage/ClassB.java
+++ b/src/main/java/com/autobump/somepackage/ClassB.java
@@ -1,6 +1,5 @@
 package com.autobump.somepackage;
-import com.google.common.collect.Multiset;
-import com.google.common.collect.ImmutableMultiset;
+import com.autobump.anotherpackage.Multiset;

 public class ClassB extends ClassA {
     public void m(Multiset s) {}
     """),

    ("Change type of parameter to array",
     "9.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassB.java b/src/main/java/com/autobump/somepackage/ClassB.java
index a0b34dc..3ecfad1 100644
--- a/src/main/java/com/autobump/somepackage/ClassB.java
+++ b/src/main/java/com/autobump/somepackage/ClassB.java
@@ -1,6 +1,6 @@
 package com.autobump.somepackage;
-import com.autobump.anotherpackage.Multiset;
+import com.google.common.collect.ImmutableMultiset;

 public class ClassB extends ClassA {
-    public void m(Multiset s) {}
+    public void m(ImmutableMultiset[] s) {}
 }
     """),

    ("Change type of array to compatible type",
     "9.0.1",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassB.java b/src/main/java/com/autobump/somepackage/ClassB.java
index 3ecfad1..da11155 100644
--- a/src/main/java/com/autobump/somepackage/ClassB.java
+++ b/src/main/java/com/autobump/somepackage/ClassB.java
@@ -1,6 +1,6 @@
 package com.autobump.somepackage;
-import com.google.common.collect.ImmutableMultiset;
+import com.google.common.collect.Multiset;

 public class ClassB extends ClassA {
-    public void m(ImmutableMultiset[] s) {}
+    public void m(Multiset[] s) {}
 }
     """),

    ("Change type of array to base type",
     "10.0.0",
     """
diff --git a/src/main/java/com/autobump/somepackage/ClassB.java b/src/main/java/com/autobump/somepackage/ClassB.java
index da11155..4e0ae94 100644
--- a/src/main/java/com/autobump/somepackage/ClassB.java
+++ b/src/main/java/com/autobump/somepackage/ClassB.java
@@ -2,5 +2,5 @@ package com.autobump.somepackage;
 import com.google.common.collect.Multiset;

 public class ClassB extends ClassA {
-    public void m(Multiset[] s) {}
+    public void m(Multiset s) {}
 }
     """)

]
