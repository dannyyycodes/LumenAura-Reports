diff --git a//dev/null b/generate_astrocartography.py
index 0000000000000000000000000000000000000000..51651887210db66532cf0316440faa152b2a6974 100644
--- a//dev/null
+++ b/generate_astrocartography.py
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
+        default="templates/astrocartography_sample.json"
+    )
+    args = parser.parse_args()
+    try:
+        with open(args.data) as f:
+            data = json.load(f)
+    except FileNotFoundError:
+        print(f"Error: {args.data} not found.")
+        sys.exit(1)
+
+    gen = PDFGenerator("output/astrocartography.pdf")
+    gen.add_title(data["title"])
+    for section in data["sections"]:
+        gen.add_section(section["title"], section["content"])
+    gen.save()
+    sys.exit(0)
+
+
+if __name__ == "__main__":
+    main()
