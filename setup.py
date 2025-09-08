# setup.py
from setuptools import setup, find_packages

setup(
    name='autonomous247',
    version='0.1.0',
    packages=find_packages(),
    author='Hamza Abu Ayyash',
    author_email='info@the-247.com',
    description='An autonomous AI agent for content creation and social media management.',
    install_requires=[
        # We let requirements.txt handle the dependencies,
        # but this file makes the project structure discoverable.
    ],
)
