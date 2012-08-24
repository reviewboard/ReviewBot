from setuptools import setup


PACKAGE = "reviewbotext"
VERSION = "0.1"

setup(
    name="Review Bot Extension",
    version=VERSION,
    description="An extension for communicating with Review Bot",
    author="Steven MacLeod",
    packages=["reviewbotext"],
    entry_points={
        'reviewboard.extensions':
            '%s = reviewbotext.extension:ReviewBotExtension' % PACKAGE,
    },
    install_requires=[
          'celery',
    ],
    package_data={
        'reviewbotext': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/admin/reviewbotext/reviewbottool/*.html',
        ],
    }
)
