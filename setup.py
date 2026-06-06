from setuptools import setup

setup(
    name="pcapprocessor",
    version="2.0.2",
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
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Networking :: Monitoring",
    ],
)
