diff --git a//dev/null b/generate_destinymatrix.py
index 0000000000000000000000000000000000000000..071bf32cc0ffa4bc35527d6a6c429a2fffb2e135 100644
--- a//dev/null
+++ b/generate_destinymatrix.py
@@ -0,0 +1,31 @@
+import argparse
+import json
+from utils.pdf_generator import PDFGenerator
+import sys
+
+
+def main():
+    parser = argparse.ArgumentParser()
+    parser.add_argument(
+        "--data",
+        help="Path to JSON data file",
+        default="templates/destinymatrix_sample.json"
+    )
+    args = parser.parse_args()
+    try:
+        with open(args.data) as f:
+            data = json.load(f)
+    except FileNotFoundError:
+        print(f"Error: {args.data} not found.")
+        sys.exit(1)
+
+    gen = PDFGenerator("output/destinymatrix.pdf")
+    gen.add_title(data["title"])
+    for section in data["sections"]:
+        gen.add_section(section["title"], section["content"])
+    gen.save()
+    sys.exit(0)
+
+
+if __name__ == "__main__":
+    main()
