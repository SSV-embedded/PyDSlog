import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PyDSlog",
    version="0.0.6",
    author="SSV Software Systems GmbH",
    author_email="fbu@ssv-embedded.de",
    description="Sensor data acquisition library.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fbussv/PyDSlog",
    packages=setuptools.find_packages(),
    install_requires=[
       'pyserial',
       'paho-mqtt'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)