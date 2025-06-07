from setuptools import setup

setup(
    name="lumenaurareports",
    version="0.1.0",
    py_modules=["report_engine", "run_report"],
    install_requires=[
        "reportlab",
        "openai"
    ],
)
