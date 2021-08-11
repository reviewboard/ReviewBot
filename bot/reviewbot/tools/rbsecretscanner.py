"""Review Bot tool to check for hard-coded security credentials."""

from __future__ import unicode_literals

import base64
import json
import re
from zlib import crc32

import six

from reviewbot.tools.base import BaseTool
from reviewbot.utils.text import base62_encode


class SecretScannerTool(BaseTool):
    """Review Bot tool to check for hard-coded secrets and credentials."""

    name = 'Secret Scanner'
    version = '1.0'
    description = (
        'Review Bot tool to check for hard-coded secrets and credentials.'
    )
    timeout = 60

    def handle_files(self, files, **kwargs):
        """Perform a review of all files.

        This will compute a regex used to match secret keys, before checking
        each individual file.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            **kwargs (dict):
                Keyword arguments passed to :py:meth:`execute`.
        """
        # This is organized in 3 sections:
        #
        # 1. Vendor-identifiable patterns
        # 2. Vendor-likely patterns (some identifier present that could
        #    potentially match something else)
        # 3. General patterns (usually just sequences of letters/numbers in
        #    some arrangement or length).
        #
        # Within each, they're listed in vendor order.
        self.pattern = re.compile(
            br"""(
            ##############################################################
            # Vendor-identifable patterns
            ##############################################################

            # AWS Access Key
            #
            # See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
            #
            # Rule updated: April 7, 2021
            (\b(?:A3T[A-Z0-9]|ABIA|ACCA|AGPA|AIDA|AIPA|AKIA|ANPA|ANVA|APKA|
            AROA|ASCA|ASIA)
            [A-Z0-9]{16}\b)
            |

            # AWS MWS Key
            #
            # Rule updated: April 7, 2021
            (amzn.mws.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}
            -[0-9a-f]{4}-[0-9a-f]{12})
            |

            # AWS Secret Key
            #
            # Rule updated: April 7, 2021
            (AWS.*\b[0-9A-Z/+]{40}\b)
            |

            # Certificate
            #
            # Rule updated: April 7, 2021
            (-----END\sCERTIFICATE-----)
            |

            # Discord WebHook URL
            #
            # Rule updated: April 7, 2021
            (https?://discord.com/api/webhooks/[A-Za-z0-9_/-]+)
            |

            # GitHub OAuth (legacy, deprecated April 2021)
            #
            # Rule updated: April 7, 2021
            (GITHUB.*\b[0-9a-zA-Z]{35,40}\b)
            |

            # GitHub OAuth (modern, as of April 2021)
            #
            # Rule updated: April 7, 2021
            (?P<github_modern_token>\b(?:gh[oprsu]_[A-Za-z0-9]{35,251})\b)
            |

            # Google (GCP) Client ID
            #
            # Rule updated: April 7, 2021
            (\d+-[a-z0-9]+\.apps\.googleusercontent\.com)
            |

            # Google (GCP) Service-account
            #
            # Rule updated: April 7, 2021
            ([A-Za-z0-9-]+@[^.]+.gserviceaccount.com)
            |
            (['"]type['"]:\s*['"]service_account['"])
            |

            # Heroku API Key
            #
            # Rule updated: April 7, 2021
            (HEROKU.*\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-
            [a-f0-9]{12}\b)
            |

            # PGP Private Key Block
            #
            # Rule updated: April 7, 2021
            (----BEGIN\sPGP\sPRIVATE\sKEY\sBLOCK----)
            |

            # PyPI API Token
            #
            # NOTE: Erring on the low side for a length. Generated keys seem
            #       to be 190+ (but it's variable).
            #
            # Rule updated: April 7, 2021
            (pypi[-:][A-Za-z0-9_]{128,})
            |

            # RSA Private Key
            #
            # Rule updated: April 7, 2021
            (----BEGIN\sRSA\sPRIVATE\sKEY----)
            |

            # SSH(DSA) Private Key
            #
            # Rule updated: April 7, 2021
            (----BEGIN\sDSA\sPRIVATE\sKEY----)
            |

            # SSH(EC) Private Key
            #
            # Rule updated: April 7, 2021
            (----BEGIN\sEC\sPRIVATE\sKEY----)
            |

            # SSH(OPENSSH) Private Key
            #
            # Rule updated: April 7, 2021
            (----BEGIN\sOPENSSH\sPRIVATE\sKEY----)
            |

            # Slack Token
            #
            # See https://api.slack.com/authentication/token-types
            #
            # Rule updated: April 7, 2021
            (\bxox(?:[bopr]|a-2)-[0-9-]{10,}-[a-z0-9]{32,}\b)
            |

            # Slack WebHooks
            #
            # Rule updated: April 7, 2021
            (https?://hooks.slack.com/)
            |

            # Stripe Access Keys
            #
            # Rule updated: April 7, 2021
            (\bsk_(?:live|test)_[A-Za-z0-9]{24,})
            |

            # Twitter OAuth
            #
            # Rule updated: April 7, 2021
            (TWITTER.*\b[0-9a-zA-Z]{35,44}\b)
            |


            ##############################################################
            # Vendor-likely patterns
            ##############################################################

            # Dropbox
            #
            # Rule Updated: April 7, 2021
            (\bsl\.Au[A-Za-z0-9_-]{133}\b)
            |
            (\b[A-Za-z0-8]{11}A{10}[A-Za-z0-9_]{43}\b)
            |

            # Discord Bot Token
            #
            # Rule updated: April 7, 2021
            (\b[A-Za-z0-9]{24}\.[A-Za-z0-9]{6}\.[A-Za-z0-9_-]{27}\b)
            |

            # Facebook Access Token
            #
            # Rule updated: April 7, 2021
            (\bEAACEdEose0cBA[0-9A-Za-z]+\b)
            |

            # Mailchimp
            #
            # Rule updated: April 7, 2021
            (\b[a-f0-9]{32}-us\d+\b)
            |

            # Mailgun
            #
            # Rule updated: April 7, 2021
            (\bkey-[a-z0-9]{32}\b)
            |

            # Twilio Account SID
            #
            # Rule updated: April 7, 2021
            (\bAC[a-z0-9]{32}\b)
            |

            # Twilio API Key
            #
            # Rule updated: April 7, 2021
            (\bSK[a-z0-9]{32}\b)
            |


            ##############################################################
            # Generic patterns
            ##############################################################

            # Asana Access Token
            #
            # Rule updated: April 7, 2021
            (\b\d/\d{13}:[a-z0-9]{32}\b)
            |

            # Google (GCP) API Key
            #
            # Rule updated: April 7, 2021
            (\b[A-Za-z0-9]{39}\b)
            |

            # JSON Web Token
            #
            # Rule updated: April 7, 2021
            (?P<json_web_token>\b[A-Za-z0-9_/-=]+\.[A-Za-z0-9_/-=]+
            \.[A-Za-z0-9_/-=]+\b)
            |

            # NPM Access Token
            #
            # Rule updated: April 7, 2021
            (\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b)

            )""", re.IGNORECASE | re.VERBOSE)

        return super(SecretScannerTool, self).handle_files(files, **kwargs)

    def handle_file(self, f, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            **kwargs (dict):
                Additional keyword arguments.
        """
        patched_file_contents = f.patched_file_contents

        if not patched_file_contents:
            return

        lines = patched_file_contents.splitlines()
        pattern = self.pattern

        for line_num, line in enumerate(lines, start=1):
            m = pattern.search(line)

            if m:
                # Some tokens have checksumming built in that allows us to
                # separate real tokens from test data. If we know of one,
                # check it now.
                is_valid = True

                for key, value in six.iteritems(m.groupdict()):
                    if value is not None:
                        validate_func = getattr(self, '_is_%s_valid' % key,
                                                None)

                        if validate_func is not None:
                            is_valid = validate_func(value, m)
                            break

                if is_valid:
                    f.comment('This line appears to contain a hard-coded '
                              'credential, which is a potential security '
                              'risk. Please verify this, and revoke the '
                              'credential if needed.',
                              first_line=line_num,
                              start_column=m.start() + 1)

    def _is_github_modern_token_valid(self, token, m):
        """Return whether a modern GitHub token is valid.

        Modern GitHub tokens (introduced in April 2021) are prefixed with a
        ``gh?_`` prefix and contain a Base62-encoded CRC32 checksum of the
        token data that follows, stored as the last 6 characters of the
        token. This allows for offline validation of real (active or inactive)
        tokens without hitting false-positives when seeing fake tokens.

        Args:
            token (bytes):
                The full token to validate.

            m (object, unused):
                The regex match data for the token.

        Returns:
            bool:
            ``True`` if the token is valid. ``False`` if it is not.
        """
        checksum = base62_encode(crc32(token[4:-6]) & 0xFFFFFFFF).zfill(6)

        return token[-6:] == checksum

    def _is_json_web_token_valid(self, token, m):
        """Return whether a token is a JSON Web Token.

        This will decode the first part of the token and see if it identifies
        as a JSON Web Token.

        Args:
            token (bytes):
                The full token to validate.

            m (object, unused):
                The regex match data for the token.

        Returns:
            bool:
            ``True`` if the token is valid. ``False`` if it is not.
        """
        header = token.split(b'.')[0]

        try:
            header = json.loads(base64.b64decode(header).decode('utf-8'))

            return header['typ'] == 'JWT'
        except Exception:
            # This isn't a JSON web token.
            return False
