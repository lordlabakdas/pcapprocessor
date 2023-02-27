from setuptools import setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="pcapprocessor",
    version="0.1.0",
    description="A simple PCAP processor",
    author="Siddharth Gangadhar, Truc Anh N Nguyen, Santosh Gondi",
    author_email="lordlabakdas.code@gmail.com",
    maintainer="Siddharth Gangadhar",
    maintainer_email="lordlabakdas.code@gmail.com",
    keywords="pcap, python, network, security, metrics, analysis",
    install_requires=requirements,
    packages=["pcapprocessor"],
)

