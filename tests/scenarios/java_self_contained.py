handler = "java_ast"

commit_history = [

    ("Initial commit",
     "1.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
new file mode 100644
index 0000000..2fb5ed5
--- /dev/null
+++ b/com/autobump/somepackage/ClassA.java
@@ -0,0 +1,3 @@
+public class ClassA {
+}
+
--
2.7.4
     """),

    ("Add public field",
     "1.1.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 2fb5ed5..9597d26 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -1,3 +1,4 @@
 public class ClassA {
+    public static final double PI = 3.14;
 }

--
2.7.4
    """),

    ("Add private field",
     "1.1.1",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 9597d26..c4dddea 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -1,4 +1,5 @@
 public class ClassA {
     public static final double PI = 3.14;
+    private static final double PHI = 1.618;
 }

--
2.7.4
     """),

    ("Add public method",
     "1.2.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index c4dddea..93eb438 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -1,5 +1,8 @@
 public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;
+
+    public void method() {
+    }
 }

--
2.7.4
    """),

    ("Add private method",
     "1.2.1",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 93eb438..a0a7096 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -4,5 +4,8 @@ public class ClassA {

     public void method() {
     }
+
+    private void internal() {
+    }
 }

--
2.7.4
    """),

    ("Add parameter to public method",
     "2.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index a0a7096..65c70bb 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -2,7 +2,7 @@ public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;

-    public void method() {
+    public void method(Object a) {
     }

     private void internal() {
--
2.7.4
    """),

    ("Add second parameter to public method",
     "3.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 65c70bb..3e901d0 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -2,7 +2,7 @@ public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;

-    public void method(Object a) {
+    public void method(Object a, Object b) {
     }

     private void internal() {
--
2.7.4
    """),

    ("Overload method",
     "3.1.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 3e901d0..add2916 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -2,6 +2,9 @@ public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;

+    public void method(Object a) {
+    }
+
     public void method(Object a, Object b) {
     }

--
2.7.4
    """),

    ("Remove public method",
     "4.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index add2916..65c70bb 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -5,9 +5,6 @@ public class ClassA {
     public void method(Object a) {
     }

-    public void method(Object a, Object b) {
-    }
-
     private void internal() {
     }
 }
--
2.7.4
    """),

    ("Define nested class",
     "4.1.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 65c70bb..05026a8 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -7,5 +7,8 @@ public class ClassA {

     private void internal() {
     }
+
+    public class NestedClass {
+    }
 }

--
2.7.4
    """),

    ("Define public field in nested class",
     "4.2.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 05026a8..a319f87 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -9,6 +9,7 @@ public class ClassA {
     }

     public class NestedClass {
+        public int amount;
     }
 }

--
2.7.4
    """),

    ("Remove nested class",
     "5.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index a319f87..cc035cb 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -7,9 +7,4 @@ public class ClassA {

     private void internal() {
     }
-
-    public class NestedClass {
-        public int amount;
-    }
 }
-
--
2.7.4
    """),

    ("Add another class in same package",
     "6.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index cc035cb..8c8829d 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -1,3 +1,5 @@
+package com.autobump.somepackage;
+
 public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;
diff --git a/com/autobump/somepackage/ClassB.java b/com/autobump/somepackage/ClassB.java
new file mode 100644
index 0000000..04304d2
--- /dev/null
+++ b/com/autobump/somepackage/ClassB.java
@@ -0,0 +1,6 @@
+package com.autobump.somepackage;
+
+public class ClassB {
+    public int x;
+    public int y;
+}
--
2.7.4
    """),

    ("Change type of parameter",
     "7.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 8c8829d..7e89666 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -4,7 +4,7 @@ public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;

-    public void method(Object a) {
+    public void method(ClassB p) {
     }

     private void internal() {
--
2.7.4
    """),

    ("Change type of parameter to subclass",
     "8.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index 7e89666..f86eb25 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -4,7 +4,7 @@ public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;

-    public void method(ClassB p) {
+    public void method(ClassB2 p) {
     }

     private void internal() {
diff --git a/com/autobump/somepackage/ClassB2.java b/com/autobump/somepackage/ClassB2.java
new file mode 100644
index 0000000..832cd45
--- /dev/null
+++ b/com/autobump/somepackage/ClassB2.java
@@ -0,0 +1,4 @@
+package com.autobump.somepackage;
+
+public class ClassB2 extends ClassB {
+}
--
2.7.4
    """),

    ("Add an interface in the same package",
     "8.1.0",
     """
diff --git a/com/autobump/somepackage/InterfaceD.java b/com/autobump/somepackage/InterfaceD.java
new file mode 100644
index 0000000..2e7ee33
--- /dev/null
+++ b/com/autobump/somepackage/InterfaceD.java
@@ -0,0 +1,4 @@
+package com.autobump.somepackage;
+
+interface InterfaceD {
+}
--
2.7.4
    """),

    ("Change type of parameter",
     "9.0.0",
     """
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index f86eb25..fb832f2 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -4,7 +4,7 @@ public class ClassA {
     public static final double PI = 3.14;
     private static final double PHI = 1.618;

-    public void method(ClassB2 p) {
+    public void method(InterfaceD d) {
     }

     private void internal() {
--
2.7.4
    """),

    ("Implement interface with class",
     "9.0.1",
     """
diff --git a/com/autobump/somepackage/ClassB2.java b/com/autobump/somepackage/ClassB2.java
index 832cd45..c098144 100644
--- a/com/autobump/somepackage/ClassB2.java
+++ b/com/autobump/somepackage/ClassB2.java
@@ -1,4 +1,4 @@
 package com.autobump.somepackage;

-public class ClassB2 extends ClassB {
+public class ClassB2 extends ClassB implements InterfaceD {
 }
--
2.7.4
    """),

    ("Import class from another package",
     "9.1.0",
     """
diff --git a/com/autobump/anotherpackage/ClassE.java b/com/autobump/anotherpackage/ClassE.java
new file mode 100644
index 0000000..9b29eab
--- /dev/null
+++ b/com/autobump/anotherpackage/ClassE.java
@@ -0,0 +1,4 @@
+package com.autobump.anotherpackage;
+
+public class ClassE {
+}
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index fb832f2..a546710 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -1,4 +1,5 @@
 package com.autobump.somepackage;
+import com.autobump.anotherpackage.ClassE;

 public class ClassA {
     public static final double PI = 3.14;
@@ -7,6 +8,9 @@ public class ClassA {
     public void method(InterfaceD d) {
     }

+    public void another(ClassE e) {
+    }
+
     private void internal() {
     }
 }
--
2.7.4
    """),

    ("Change type to compatible one and add new feature",
     "9.2.0",
     """
diff --git a/com/autobump/anotherpackage/ClassE.java b/com/autobump/anotherpackage/ClassE.java
index 9b29eab..925f95f 100644
--- a/com/autobump/anotherpackage/ClassE.java
+++ b/com/autobump/anotherpackage/ClassE.java
@@ -1,4 +1,4 @@
 package com.autobump.anotherpackage;

-public class ClassE {
+public class ClassE implements InterfaceE {
 }
diff --git a/com/autobump/anotherpackage/InterfaceE.java b/com/autobump/anotherpackage/InterfaceE.java
new file mode 100644
index 0000000..f9d3d60
--- /dev/null
+++ b/com/autobump/anotherpackage/InterfaceE.java
@@ -0,0 +1,4 @@
+package com.autobump.anotherpackage;
+
+public interface InterfaceE {
+}
diff --git a/com/autobump/somepackage/ClassA.java b/com/autobump/somepackage/ClassA.java
index a546710..cd9d07e 100644
--- a/com/autobump/somepackage/ClassA.java
+++ b/com/autobump/somepackage/ClassA.java
@@ -1,5 +1,6 @@
 package com.autobump.somepackage;
 import com.autobump.anotherpackage.ClassE;
+import com.autobump.anotherpackage.InterfaceE;

 public class ClassA {
     public static final double PI = 3.14;
@@ -8,7 +9,7 @@ public class ClassA {
     public void method(InterfaceD d) {
     }

-    public void another(ClassE e) {
+    public void another(InterfaceE e) {
     }

     private void internal() {
--
2.7.4
    """),

]
