from setuptools import setup, find_packages
from distutils.spawn import spawn, find_executable


PACKAGE_NAME = "ReviewBot"
VERSION = "0.1"

cppcheck = find_executable("cppcheck")
if not cppcheck:
    print "You do not have cppcheck installed or in your search path."
    print "Please try: sudo apt-get install cppcheck."
    print "Or for a more upto date version please goto: http://sourceforge.net/projects/cppcheck/"
    exit()

cpplint = find_executable("cpplint.py")
if not cpplint:
    print "You do not have cpplint.py installed or in your search path."
    print "Please get the script from here: http://google-styleguide.googlecode.com/svn/trunk/cpplint/cpplint.py."
    print "Try wget http://google-styleguide.googlecode.com/svn/trunk/cpplint/cpplint.py"
    exit()

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description="ReviewBot, the automated code reviewer",
    author="Steven MacLeod, Daniel Laird",
    author_email="steven@smacleod.ca",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'reviewbot = reviewbot.celery:main'
        ],
        'reviewbot.tools': [
            'pep8 = reviewbot.tools.pep8:pep8Tool',
            'cpplint = reviewbot.tools.cpplint:cpplintTool',
            'cppcheck = reviewbot.tools.cppcheck:cppcheckTool',
        ],
    },
    install_requires=[
        'distutils2',
        'celery>=3.0',
        'pep8>=0.7.0',
    ],)
