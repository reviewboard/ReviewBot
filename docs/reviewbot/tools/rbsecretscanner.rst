.. _tool-rbcredentialchecker:

==============
Secret Scanner
==============

.. versionadded:: 3.0

Secret Scanner is a native tool provided by Review Bot that checks files for
hard-coded security credentials, such as API tokens, encryption keys, account
identifiers, and URLs.

Note that some secrets have a well-defined format that can be verified, while
others have a higher chance of conflicting with various forms of legitimate
data.

It is up to the author of a change to verify whether they have leaked a
secret, and to revoke that secret on any affected services.


Supported File Types
====================

All files are supported by this tool, and will be checked for secrets.


Supported Secrets
=================

The following types of secrets are checked.

* AWS Access Keys
* AWS MWS Keys
* AWS Secret Keys
* Asana Access Tokens
* Discord Bot Tokens
* Discord WebHook URLs
* Dropbox Tokens
* Facebook Access Tokens
* GitHub OAuth Tokens (legacy format deprecated in April 2021)
* GitHub OAuth Tokens (modern format introduced in April 2021)
* Google (GCP) API Keys
* Google (GCP) Client IDs
* Google (GCP) Service Accounts
* Heroku API Keys
* JSON Web Tokens
* Mailchimp API Keys
* Mailgun API Keys
* NPM Access Tokens
* PGP Private Keys
* PyPI API Tokens
* RSA Private Keys
* SSH (DSA, EC, and OPENSSH) Private Keys
* SSL Certificates
* Slack Tokens
* Slack WebHook URLs
* Stripe Access Keys
* Twilio API Keys
* Twilio Account SIDs
* Twitter OAuth Tokens


Installation
============

This tool ships with Review Bot 3.0 and higher. No additional installation
is required.


Configuration
=============

Enabling Secret Scanner in Review Board
---------------------------------------

You'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

There are no configuration options available for this tool.
