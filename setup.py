from setuptools import setup, find_packages
import agieval


def readme():
    with open('README_zh.md', encoding='utf-8') as f:
        content = f.read()
    return content

 # Read dependencies from requirements.txt
def get_requirements():
    with open('requirements.txt', encoding='utf-8') as f:
        requirements = []
        for line in f.read().splitlines():
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                requirements.append(line)
        # Filter out optional dependencies (lines starting with # in requirements.txt are comments)
        return requirements

setup(
    name="agieval",
    version=agieval.__version__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'agieval=agieval.cli.cli:main'
        ],
    },
    python_requires='>=3.11',
    install_requires=get_requirements(),
    long_description=readme(),
    long_description_content_type='text/markdown',
)