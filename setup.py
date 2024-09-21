from setuptools import setup, find_packages

# IMPORTANT: this must be enabled via pip using the command `pip install -e .` (remember to include the dot at the end of command).

setup(
    name="githubanalysis",
    version="1.0",
    description="Code for analysing research software github repositories",
    author="Flic Anderson",
    packages=find_packages(),
    #    package_dir={'githubanalysis': 'githubanalysis'}
)

# via https://stackoverflow.com/a/50194143


# setup(
#    name='zenodocode',
#    version='1.0',
#    description='Code for obtaining github repositories from DOIs on zenodo',
#    author='Flic Anderson',
#    packages=find_packages()
# )
