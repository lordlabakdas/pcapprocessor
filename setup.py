from setuptools import setup

setup(
    name="pcapprocessor",
    version="2.0.0",
    description="A simple PCAP processor",
    author="Siddharth Gangadhar, Truc Anh N Nguyen, Santosh Gondi",
    author_email="lordlabakdas.code@gmail.com",
    maintainer="Siddharth Gangadhar",
    maintainer_email="lordlabakdas.code@gmail.com",
    keywords="pcap, python, network, security, metrics, analysis",
    install_requires=[
        "numpy",
        "scipy",
        "pyshark",
        "matplotlib",
        "seaborn",
    ],
    packages=["pcapprocessor"],
)
