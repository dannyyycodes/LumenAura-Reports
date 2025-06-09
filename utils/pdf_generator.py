diff --git a//dev/null b/utils/pdf_generator.py
index 0000000000000000000000000000000000000000..293679738974b2d39dd49ea35573a634a56fe325 100644
--- a//dev/null
+++ b/utils/pdf_generator.py
@@ -0,0 +1,22 @@
+from reportlab.lib.pagesizes import LETTER
+from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
+from reportlab.lib.styles import getSampleStyleSheet
+
+
+class PDFGenerator:
+    def __init__(self, path):
+        self.doc = SimpleDocTemplate(path, pagesize=LETTER)
+        self.elements = []
+        self.styles = getSampleStyleSheet()
+
+    def add_title(self, title: str) -> None:
+        self.elements.append(Paragraph(title, self.styles["Title"]))
+        self.elements.append(Spacer(1, 12))
+
+    def add_section(self, title: str, content: str) -> None:
+        self.elements.append(Paragraph(title, self.styles["Heading2"]))
+        self.elements.append(Paragraph(content, self.styles["BodyText"]))
+        self.elements.append(Spacer(1, 12))
+
+    def save(self) -> None:
+        self.doc.build(self.elements)
