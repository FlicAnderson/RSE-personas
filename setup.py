from setuptools import setup, find_packages

setup(
    name='githubanalysis',
    version='1.0',
    description='Code for analysing research software github repositories',
    author='Flic Anderson',
    packages=find_packages(),
    package_dir={'githubanalysis': 'code/githubanalysis'}
)

# via https://stackoverflow.com/a/50194143