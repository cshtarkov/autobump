commit_history = [

    ("Initial commit",
     "1.0.0",
     """
diff --git a/module_a.py b/module_a.py
new file mode 100644
index 0000000..ab92b1d
--- /dev/null
+++ b/module_a.py
@@ -0,0 +1,2 @@
+def func_1():
+    pass
--
2.7.4
     """),

    ("Add non-optional parameter",
     "2.0.0",
     """
diff --git a/module_a.py b/module_a.py
index ab92b1d..f700cc9 100644
--- a/module_a.py
+++ b/module_a.py
@@ -1,2 +1,2 @@
-def func_1():
+def func_1(a):
     pass
--
2.7.4
     """),

    ("Add optional parameter",
     "2.1.0",
     """
diff --git a/module_a.py b/module_a.py
index f700cc9..65937be 100644
--- a/module_a.py
+++ b/module_a.py
@@ -1,2 +1,2 @@
-def func_1(a):
+def func_1(a, b=3):
     pass
--
2.7.4
     """),

    ("Add private function",
     "2.1.1",
     """
diff --git a/module_a.py b/module_a.py
index 65937be..a124792 100644
--- a/module_a.py
+++ b/module_a.py
@@ -1,2 +1,5 @@
 def func_1(a, b=3):
     pass
+
+def _func_2(a, b, c):
+    pass
--
2.7.4
     """),

    ("Add public function",
     "2.2.0",
     """
diff --git a/module_a.py b/module_a.py
index a124792..c58c9f8 100644
--- a/module_a.py
+++ b/module_a.py
@@ -3,3 +3,7 @@ def func_1(a, b=3):

 def _func_2(a, b, c):
     pass
+
+def func_3(a, b, c):
+    pass
+
--
2.7.4
     """),

    ("Remove public function",
     "3.0.0",
     """
diff --git a/module_a.py b/module_a.py
index c58c9f8..c466a53 100644
--- a/module_a.py
+++ b/module_a.py
@@ -1,6 +1,3 @@
-def func_1(a, b=3):
-    pass
-
 def _func_2(a, b, c):
     pass

--
2.7.4
     """),

    ("Add private class",
     "3.0.1",
     """
diff --git a/module_a.py b/module_a.py
index c466a53..b510291 100644
--- a/module_a.py
+++ b/module_a.py
@@ -4,3 +4,5 @@ def _func_2(a, b, c):
 def func_3(a, b, c):
     pass

+class _Class1(object):
+    pass
--
2.7.4
     """),

    ("Add public class",
     "3.1.0",
     """
diff --git a/module_a.py b/module_a.py
index b510291..032d291 100644
--- a/module_a.py
+++ b/module_a.py
@@ -6,3 +6,7 @@ def func_3(a, b, c):

 class _Class1(object):
     pass
+
+class Class2(object):
+    def method1(self):
+        pass
--
2.7.4
     """),

    ("Add private method",
     "3.1.1",
     """
diff --git a/module_a.py b/module_a.py
index 032d291..a12771c 100644
--- a/module_a.py
+++ b/module_a.py
@@ -10,3 +10,6 @@ class _Class1(object):
 class Class2(object):
     def method1(self):
         pass
+
+    def _method2(self):
+        pass
--
2.7.4
     """),

    ("Remove public method",
     "4.0.0",
     """
diff --git a/module_a.py b/module_a.py
index a12771c..b335440 100644
--- a/module_a.py
+++ b/module_a.py
@@ -8,8 +8,5 @@ class _Class1(object):
     pass

 class Class2(object):
-    def method1(self):
-        pass
-
     def _method2(self):
         pass
--
2.7.4
     """),

    ("Add new module",
     "4.1.0",
     """
diff --git a/module_b.py b/module_b.py
new file mode 100644
index 0000000..ab92b1d
--- /dev/null
+++ b/module_b.py
@@ -0,0 +1,2 @@
+def func_1():
+    pass
--
2.7.4
     """),

    ("Remove module",
     "5.0.0",
     """
diff --git a/module_b.py b/module_b.py
deleted file mode 100644
index ab92b1d..0000000
--- a/module_b.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def func_1():
-    pass
--
2.7.4
     """),

    ("Implement function",
     "5.0.1",
     """
diff --git a/module_a.py b/module_a.py
index b335440..14753c1 100644
--- a/module_a.py
+++ b/module_a.py
@@ -2,7 +2,7 @@ def _func_2(a, b, c):
     pass

 def func_3(a, b, c):
-    pass
+    return a, b, c

 class _Class1(object):
     pass
--
2.7.4
     """),

    ("Add constant",
     "5.1.0",
     """
diff --git a/module_a.py b/module_a.py
index 14753c1..47c8948 100644
--- a/module_a.py
+++ b/module_a.py
@@ -1,3 +1,5 @@
+PI = 3.14
+
 def _func_2(a, b, c):
     pass

--
2.7.4
     """),

    ("Add public inner class",
     "5.2.0",
     """
diff --git a/module_a.py b/module_a.py
index 47c8948..671020d 100644
--- a/module_a.py
+++ b/module_a.py
@@ -12,3 +12,6 @@ class _Class1(object):
 class Class2(object):
     def _method2(self):
         pass
+
+    class Inner(object):
+        pass
--
2.7.4
     """),

    ("Add private inner class",
     "5.2.1",
     """
diff --git a/module_a.py b/module_a.py
index 671020d..c43dc72 100644
--- a/module_a.py
+++ b/module_a.py
@@ -15,3 +15,6 @@ class Class2(object):

     class Inner(object):
         pass
+
+    class _PrivateInner(object):
+        pass
--
2.7.4
     """),

    ("Remove public inner class",
     "6.0.0",
     """
diff --git a/module_a.py b/module_a.py
index c43dc72..125a0f3 100644
--- a/module_a.py
+++ b/module_a.py
@@ -13,8 +13,5 @@ class Class2(object):
     def _method2(self):
         pass

-    class Inner(object):
-        pass
-
     class _PrivateInner(object):
         pass
--
2.7.4
     """),

    ("Change type of parameters",
     "7.0.0",
     """
diff --git a/module_a.py b/module_a.py
index 125a0f3..9903cd6 100644
--- a/module_a.py
+++ b/module_a.py
@@ -4,6 +4,7 @@ def _func_2(a, b, c):
     pass

 def func_3(a, b, c):
+    a.method(b, c)
     return a, b, c

 class _Class1(object):
--
2.7.4
     """)

]
