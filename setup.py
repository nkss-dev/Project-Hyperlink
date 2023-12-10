from setuptools import setup

requirements = []
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

readme = ""
with open("README.md") as f:
    readme = f.read()

setup(
    name="project-hyperlink",
    author="GetPsyched",
    url="https://github.com/GetPsyched/project-hyperlink",
    project_urls={
        "Issue tracker": "https://github.com/GetPsyched/project-hyperlink/issues",
    },
    version="2.0.0",
    license="MIT",
    description="A Discord bot for servers based around NITKKR",
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    python_requires=">=3.11.0",
)
