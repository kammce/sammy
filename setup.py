import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sammy-sjsu-dev2",
    version="0.1.1",
    author="SJSU-Dev2 Organization",
    description="A tool for managing SJSU-Dev2 firmware projects and to install external packages such as platforms and libraries.",long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SJSU-Dev2/sammy/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
    ],
    entry_points={
        'console_scripts': ['sammy=sammy.sammy:main'],
    },
    python_requires='>=3.9',
    install_requires=[
      'click>=8.0',
      'giturlparse>=0.10.0',
      'requests>=2.25.1',
    ]
)
