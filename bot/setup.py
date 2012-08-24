from setuptools import setup, find_packages

PACKAGE_NAME = "ReviewBot"
VERSION = "0.1"


setup(name=PACKAGE_NAME,
      version=VERSION,
      description="ReviewBot, the automated code reviewer",
      author="Steven MacLeod",
      author_email="steven@smacleod.ca",
      packages=find_packages(),
      entry_points={
          'reviewbot.tools': [
              'pep8 = reviewbot.tools.pep8:pep8Tool',
          ]
      },
      install_requires=[
          'celery>=2.5',
          'pep8>=0.7.0',
      ],
)
