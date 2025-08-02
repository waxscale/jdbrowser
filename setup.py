from setuptools import setup, find_packages

setup(
    name="jdbrowser",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PySide6>=5.15.2',
    ],
    author="xAI",
    description="A file browser application with tag management using PySide6",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'jdbrowser = jdbrowser.main:main',
        ],
    },
)