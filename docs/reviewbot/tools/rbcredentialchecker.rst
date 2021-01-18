.. _tool-rbcredentialchecker:

==================
Credential Checker
==================

Credential Checker is a tool for Review Bot to check for hard-coded security
credentials.


Checks
======

Credential Checker uses regex patterns to match the credentials. The result
might contain false positives.

Currently, the following credential types could be detected:

* AWS Access Key
* AWS MWS Key
* AWS Secret Key
* Facebook Access Token
* GitHub OAuth
* Google (GCP) Service-account
* Heroku API Key
* PGP Private Key Block
* RSA Private Key
* SSH(DSA) Private Key
* SSH(EC) Private Key
* SSH(OPENSSH) Private Key
* Slack Token
* Twitter OAuth