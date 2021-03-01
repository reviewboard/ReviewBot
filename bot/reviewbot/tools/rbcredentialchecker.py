"""Review Bot tool to check for hard-coded security credentials."""

from __future__ import unicode_literals

import re

from reviewbot.tools import Tool


class CredentialCheckerTool(Tool):
    """Review Bot tool to check for hard-coded security credentials."""

    name = 'Credential Checker'
    version = '1.0'
    description = ('Review Bot tool to check for hard-coded security '
                   'credentials.')
    timeout = 60

    def __init__(self):
        """Initialize the tool."""
        super(CredentialCheckerTool, self).__init__()
        self.pattern = re.compile(
            br"""(

            # AWS Access Key
            ((A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|
            ANVA|ASIA)[A-Z0-9]{16})
            |

            # AWS MWS Key
            (amzn.mws.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}
            -[0-9a-f]{4}-[0-9a-f]{12})
            |

            # AWS Secret Key
            (AWS.*[0-9A-Z/+]{40})
            |

            # Facebook Access Token
            (EAACEdEose0cBA[0-9A-Za-z]+)
            |

            # GitHub OAuth
            (GITHUB.*[0-9a-zA-Z]{35,40})
            |

            # Google (GCP) Service-account
            (\"type\": \"service_account\")
            |

            # Heroku API Key
            (HEROKU.*[0-9A-F]{8}-
            [0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A
            -F]{12})
            |

            # PGP Private Key Block
            (----BEGIN PGP PRIVATE KEY BLOCK----)
            |

            # RSA Private Key
            (----BEGIN RSA PRIVATE KEY----)
            |

            # SSH(DSA) Private Key
            (----BEGIN DSA PRIVATE KEY----)
            |

            # SSH(EC) Private Key
            (----BEGIN EC PRIVATE KEY----)
            |

            # SSH(OPENSSH) Private Key
            (----BEGIN OPENSSH PRIVATE KEY----)
            |

            # Slack Token
            (xox[pboa]-[0-9]{12}-[0-9]{12}-[0-9]{12}
            -[a-z0-9]{32})
            |

            # Twitter OAuth
            (TWITTER.*[0-9a-zA-Z]{35,44})

            )""", re.IGNORECASE | re.VERBOSE)

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        patched_file_contents = f.patched_file_contents

        if not patched_file_contents:
            return

        lines = patched_file_contents.splitlines()

        for i, line in enumerate(lines):
            if self.pattern.search(line):
                f.comment(('This line appears to contain a hard-coded '
                           'credential, which is a potential security '
                           'risk.'), i + 1)
