import setuptools

with open("README.md") as rm:
    long_description = rm.read()

setuptools.setup(
    name="hubitatmaker",
    version="0.3.2",
    author="Jason Cheatham",
    author_email="j.cheatham@gmail.com",
    description="A library for interfacing with Hubitat via its Maker API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jason0x43/hubitatmaker",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["aiohttp>=3", "getmac==0.8.2"],
    python_requires=">=3.6",
    package_data={"hubitatmaker": ["py.typed"]},
)
