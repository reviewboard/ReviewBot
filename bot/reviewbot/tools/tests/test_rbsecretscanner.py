"""Unit tests for reviewbot.tools.rbsecretscanner."""

from __future__ import unicode_literals

import six

from reviewbot.tools.rbsecretscanner import SecretScannerTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test)
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class SecretScannerToolTests(BaseToolTestCase):
    """Unit tests for SecretScannerTool."""

    tool_class = SecretScannerTool

    def test_get_can_handle_file(self):
        """Testing SecretScannerTool.get_can_handle_file"""
        self.assertTrue(self.run_get_can_handle_file(filename='test.txt'))
        self.assertTrue(self.run_get_can_handle_file(filename='test'))
        self.assertTrue(self.run_get_can_handle_file(filename='test.py'))

    @integration_test()
    def test_execute_with_asana_access_token(self):
        """Testing SecretScannerTool.execute with Asana Access Token"""
        self._run_token_test(
            '1/1234567890123:abcdefghijklmnopqrsxyz1234567890')
        self._run_token_test(
            'Z1/1234567890123:abcdefghijklmnopqrsxyz1234567890',
            match=False)
        self._run_token_test(
            '1/1234567890123:abcdefghijklmnopqrsxyz1234567890Z',
            match=False)

    @integration_test()
    def test_execute_with_aws_access_key_a3t(self):
        """Testing SecretScannerTool.execute with AWS Access Key (A3T...)
        """
        self._run_token_test('A3TA1234567890ABCDEF')
        self._run_token_test('ZA3TA1234567890ABCDEF', match=False)
        self._run_token_test('A3TA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_abia(self):
        """Testing SecretScannerTool.execute with AWS Access Key (ABIA...)
        """
        self._run_token_test('ABIA1234567890ABCDEF')
        self._run_token_test('ZABIA1234567890ABCDEF', match=False)
        self._run_token_test('ABIA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_acca(self):
        """Testing SecretScannerTool.execute with AWS Access Key (ACCA...)
        """
        self._run_token_test('ACCA1234567890ABCDEF')
        self._run_token_test('ZACCA1234567890ABCDEF', match=False)
        self._run_token_test('ACCA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_agpa(self):
        """Testing SecretScannerTool.execute with AWS Access Key (AGPA...)
        """
        self._run_token_test('AGPA1234567890ABCDEF')
        self._run_token_test('ZAGPA1234567890ABCDEF', match=False)
        self._run_token_test('AGPA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_aida(self):
        """Testing SecretScannerTool.execute with AWS Access Key (AIDA...)
        """
        self._run_token_test('AIDA1234567890ABCDEF')
        self._run_token_test('ZAIDA1234567890ABCDEF', match=False)
        self._run_token_test('AIDA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_aipa(self):
        """Testing SecretScannerTool.execute with AWS Access Key (AIPA...)
        """
        self._run_token_test('AIPA1234567890ABCDEF')
        self._run_token_test('ZAIPA1234567890ABCDEF', match=False)
        self._run_token_test('AIPA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_akia(self):
        """Testing SecretScannerTool.execute with AWS Access Key (AKIA...)
        """
        self._run_token_test('AKIA1234567890ABCDEF')
        self._run_token_test('ZAKIA1234567890ABCDEF', match=False)
        self._run_token_test('AKIA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_anpa(self):
        """Testing SecretScannerTool.execute with AWS Access Key (ANPA...)
        """
        self._run_token_test('ANPA1234567890ABCDEF')
        self._run_token_test('ZANPA1234567890ABCDEF', match=False)
        self._run_token_test('ANPA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_anva(self):
        """Testing SecretScannerTool.execute with AWS Access Key (ANVA...)
        """
        self._run_token_test('ANVA1234567890ABCDEF')
        self._run_token_test('ZANVA1234567890ABCDEF', match=False)
        self._run_token_test('ANVA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_apka(self):
        """Testing SecretScannerTool.execute with AWS Access Key (APKA...)
        """
        self._run_token_test('APKA1234567890ABCDEF')
        self._run_token_test('ZAPKA1234567890ABCDEF', match=False)
        self._run_token_test('APKA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_aroa(self):
        """Testing SecretScannerTool.execute with AWS Access Key (AROA...)
        """
        self._run_token_test('AROA1234567890ABCDEF')
        self._run_token_test('ZAROA1234567890ABCDEF', match=False)
        self._run_token_test('AROA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_asca(self):
        """Testing SecretScannerTool.execute with AWS Access Key (ASCA...)
        """
        self._run_token_test('ASCA1234567890ABCDEF')
        self._run_token_test('ZASCA1234567890ABCDEF', match=False)
        self._run_token_test('ASCA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_access_key_asia(self):
        """Testing SecretScannerTool.execute with AWS Access Key (ASIA...)
        """
        self._run_token_test('ASIA1234567890ABCDEF')
        self._run_token_test('ZASIA1234567890ABCDEF', match=False)
        self._run_token_test('ASIA1234567890ABCDEFZ', match=False)

    @integration_test()
    def test_execute_with_aws_mws_key(self):
        """Testing SecretScannerTool.execute with AWS MWS Key"""
        self._run_token_test(
            'amzn.mws.1234abcd-12ab-34de-56fa-123456abcdef')

    @integration_test()
    def test_execute_with_aws_secret_key(self):
        """Testing SecretScannerTool.execute with AWS Secret Key"""
        self._run_token_test(
            'AWS_SECRET_KEY="1234567890+ABCDEFGHIJ+1234567890+TUVWXYZ')

    @integration_test()
    def test_execute_with_certificate(self):
        """Testing SecretScannerTool.execute with certificate"""
        self._run_token_test('-----END CERTIFICATE-----')

    @integration_test()
    def test_execute_with_discord_bot_token(self):
        """Testing SecretScannerTool.execute with Discord Bot Token"""
        self._run_token_test(
            'ABCDEFGHabcdefgh12345678.ABcd12.abcdefgh_ABCDEFGH-123456789')

    @integration_test()
    def test_execute_with_discord_webhook_url(self):
        """Testing SecretScannerTool.execute with Discord WebHook URL"""
        self._run_token_test(
            'https://discord.com/api/webhooks/1234567890/abcdefghijklmnopq'
            'rstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ-123456789')
        self._run_token_test(
            'http://discord.com/api/webhooks/1234567890/abcdefghijklmnopq'
            'rstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ-123456789')

    @integration_test()
    def test_execute_with_dropbox_short_lived_access_token(self):
        """Testing SecretScannerTool.execute with Dropbox Short-Lived
        Access Token
        """
        self._run_token_test(
            'sl.Auabcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
            '1234567890-abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTU'
            'VWXZ_123456789_ABCDE')
        self._run_token_test(
            'Zsl.Auabcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
            '1234567890-abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTU'
            'VWXZ_123456789_ABCDE',
            match=False)

    @integration_test()
    def test_execute_with_facebook_access_token(self):
        """Testing SecretScannerTool.execute with Facebook Access Token"""
        self._run_token_test('EAACEdEose0cBA1234567890ABCDwxyz')
        self._run_token_test('ZEAACEdEose0cBA1234567890ABCDwxyz',
                             match=False)

    @integration_test()
    def test_execute_with_github_legacy_oauth_token(self):
        """Testing SecretScannerTool.execute with legacy GitHub OAuth
        Token
        """
        # Lower bounds of length.
        self._run_token_test(
            'GITHUB_TOKEN=1234567890ABCDEFGabcdefg12345XYZxyz')

        # Upper bounds of length.
        self._run_token_test(
            'GITHUB_TOKEN=1234567890ABCDEFGabcdefg12345XYZxyz12345')

    @integration_test()
    def test_execute_with_github_oauth_token_gho(self):
        """Testing SecretScannerTool.execute with GitHub token (gho...)"""
        # Lower bounds of length.
        self._run_token_test(
            'gho_1234567890ABCDEFGabcdefg1234508vKGb')

        # Upper bounds of length.
        self._run_token_test(
            'gho_1234567890abcdef1234567890abcdef1234567890abcdef1234567890a'
            'bcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            'abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456789'
            '0abcdef1234567890abcdef1234567890abcdef1234567890abcdef123451X8'
            '8A8')

        # Real-world (invalidated) token.
        self._run_token_test(
            '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')

        # Don't match these.
        self._run_token_test(
            'Zgho_1234567890ABCDEFGabcdefg1234508vKGb',
            match=False)
        self._run_token_test(
            'gho_1234567890ABCDEFGabcdefg1234508vKGbZ',
            match=False)

    @integration_test()
    def test_execute_with_github_oauth_token_ghp(self):
        """Testing SecretScannerTool.execute with GitHub token (ghp...)"""
        # Lower bounds of length.
        self._run_token_test(
            'ghp_1234567890ABCDEFGabcdefg1234508vKGb')

        # Upper bounds of length.
        self._run_token_test(
            'ghp_1234567890abcdef1234567890abcdef1234567890abcdef1234567890a'
            'bcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            'abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456789'
            '0abcdef1234567890abcdef1234567890abcdef1234567890abcdef123451X8'
            '8A8')

        # Real-world (invalidated) token.
        self._run_token_test(
            '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')

        # Don't match these.
        self._run_token_test(
            'Zghp_1234567890ABCDEFGabcdefg1234508vKGb',
            match=False)
        self._run_token_test(
            'ghp_1234567890ABCDEFGabcdefg1234508vKGbZ',
            match=False)

    @integration_test()
    def test_execute_with_github_oauth_token_ghr(self):
        """Testing SecretScannerTool.execute with GitHub token (ghr...)"""
        # Lower bounds of length.
        self._run_token_test(
            'ghr_1234567890ABCDEFGabcdefg1234508vKGb')

        # Upper bounds of length.
        self._run_token_test(
            'ghr_1234567890abcdef1234567890abcdef1234567890abcdef1234567890a'
            'bcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            'abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456789'
            '0abcdef1234567890abcdef1234567890abcdef1234567890abcdef123451X8'
            '8A8')

        # Real-world (invalidated) token.
        self._run_token_test(
            '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')

        # Don't match these.
        self._run_token_test(
            'Zghr_1234567890ABCDEFGabcdefg1234508vKGb',
            match=False)
        self._run_token_test(
            'ghr_1234567890ABCDEFGabcdefg1234508vKGbZ',
            match=False)

    @integration_test()
    def test_execute_with_github_oauth_token_ghs(self):
        """Testing SecretScannerTool.execute with GitHub token (ghs...)"""
        # Lower bounds of length.
        self._run_token_test(
            'ghs_1234567890ABCDEFGabcdefg1234508vKGb')

        # Upper bounds of length.
        self._run_token_test(
            'ghs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890a'
            'bcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            'abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456789'
            '0abcdef1234567890abcdef1234567890abcdef1234567890abcdef123451X8'
            '8A8')

        # Real-world (invalidated) token.
        self._run_token_test(
            'ghs_Anawk3Qg2P7at173OpuF29DF2SMEDv0ZBObL')

        # Don't match these.
        self._run_token_test(
            'Zghs_1234567890ABCDEFGabcdefg1234508vKGb',
            match=False)
        self._run_token_test(
            'ghs_1234567890ABCDEFGabcdefg1234508vKGbZ',
            match=False)

    @integration_test()
    def test_execute_with_github_oauth_token_ghu(self):
        """Testing SecretScannerTool.execute with GitHub token (ghu...)"""
        # Lower bounds of length.
        self._run_token_test(
            'ghu_1234567890ABCDEFGabcdefg1234508vKGb')

        # Upper bounds of length.
        self._run_token_test(
            'ghu_1234567890abcdef1234567890abcdef1234567890abcdef1234567890a'
            'bcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            'abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456789'
            '0abcdef1234567890abcdef1234567890abcdef1234567890abcdef123451X8'
            '8A8')

        # Real-world (invalidated) token.
        self._run_token_test(
            'ghu_EvjxC2hvFZtSn6bsKAMTWkKsTpdJ0f2fYhqu')

        # Don't match these.
        self._run_token_test(
            'Zghu_1234567890ABCDEFGabcdefg1234508vKGb',
            match=False)
        self._run_token_test(
            'ghu_1234567890ABCDEFGabcdefg1234508vKGbZ',
            match=False)

    @integration_test()
    def test_execute_with_google_gcp_api_key(self):
        """Testing SecretScannerTool.execute with Google GCP API Key"""
        self._run_token_test('ABCDEFGabcdefg123456789ZYXWzywxSTUVstuv')
        self._run_token_test('ZABCDEFGabcdefg123456789ZYXWzywxSTUVstuv',
                             match=False)
        self._run_token_test('ABCDEFGabcdefg123456789ZYXWzywxSTUVstuvZ',
                             match=False)

    @integration_test()
    def test_execute_with_google_gcp_client_id(self):
        """Testing SecretScannerTool.execute with Google GCP Client ID"""
        self._run_token_test(
            '1234567890123-abcdefghijklmnopqrstuvwxyz123456.apps.'
            'googleusercontent.com')

    @integration_test()
    def test_execute_with_google_gcp_service_account_config(self):
        """Testing SecretScannerTool.execute with Google GCP Service
        Account configuration
        """
        self._run_token_test('"type": "service_account"')
        self._run_token_test("'type': 'service_account'")

    @integration_test()
    def test_execute_with_google_gcp_service_account_id(self):
        """Testing SecretScannerTool.execute with Google GCP Service
        Account e-mail ID
        """
        self._run_token_test('my-service@appspot.gserviceaccount.com')
        self._run_token_test('my-service@developer.gserviceaccount.com')

    @integration_test()
    def test_execute_with_heroku_api_key(self):
        """Testing SecretScannerTool.execute with Heroku API Key"""
        self._run_token_test(
            'HEROKU_API_KEY=1234abcd-12ab-34cd-56ef-123456abcdef')

    @integration_test()
    def test_execute_with_json_web_token(self):
        """Testing SecretScannerTool.execute with JSON Web Token"""
        self._run_token_test(
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ2YWx1ZSJ9.'
            '5pps1XMxciBCpOhezqTk9XuGny-4_HZ9aEKp3AqgekA')
        self._run_token_test(
            'W10K.eyJrZXkiOiJ2YWx1ZSJ9.8nUniKZ63ZQLtj401tAGgVLo0Fm1LAOe'
            'M5vPSBY3-os',
            match=False)
        self._run_token_test(
            'eyJ0eXAiOiAib3RoZXIifQo=.eyJrZXkiOiJ2YWx1ZSJ9.'
            '8nUniKZ63ZQLtj401tAGgVLo0Fm1LAOeM5vPSBY3-os',
            match=False)
        self._run_token_test(
            'foo.bar.baz',
            match=False)

    @integration_test()
    def test_execute_with_mailchimp_api_key(self):
        """Testing SecretScannerTool.execute with Mailchimp API key"""
        self._run_token_test('abcdef1234567890abcdef1234567890-us1')
        self._run_token_test('abcdef1234567890abcdef1234567890-us12')
        self._run_token_test('Zabcdef1234567890abcdef1234567890-us12',
                             match=False)
        self._run_token_test('abcdef1234567890abcdef1234567890-us12Z',
                             match=False)

    @integration_test()
    def test_execute_with_mailgun_api_key(self):
        """Testing SecretScannerTool.execute with Mailgun API key"""
        self._run_token_test('key-abcdefghijklmnopqrstuvwxyz123456')
        self._run_token_test('Zkey-abcdefghijklmnopqrstuvwxyz123456',
                             match=False)
        self._run_token_test('key-abcdefghijklmnopqrstuvwxyz123456Z',
                             match=False)

    @integration_test()
    def test_execute_with_npm_access_token(self):
        """Testing SecretScannerTool.execute with NPM Access Token"""
        self._run_token_test('abcd1234-ab12-cd34-ef56-abcdef123456')
        self._run_token_test('Zabcd1234-ab12-cd34-ef56-abcdef123456',
                             match=False)
        self._run_token_test('abcd1234-ab12-cd34-ef56-abcdef123456Z',
                             match=False)

    @integration_test()
    def test_execute_with_pgp_private_key(self):
        """Testing SecretScannerTool.execute with PGP Private Key"""
        self._run_token_test('----BEGIN PGP PRIVATE KEY BLOCK----')

    @integration_test()
    def test_execute_with_pypi_api_token(self):
        """Testing SecretScannerTool.execute with PyAPI API Token"""
        self._run_token_test(
            'pypi-abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
            '0123456789_abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRST'
            'UVWXYZ_0123456789_abcdefghijklmnopqrstuvwxyz')
        self._run_token_test(
            'pypi:abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
            '0123456789_abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRST'
            'UVWXYZ_0123456789_abcdefghijklmnopqrstuvwxyz')

    @integration_test()
    def test_execute_with_rsa_private_key(self):
        """Testing SecretScannerTool.execute with RSA Private Key"""
        self._run_token_test('----BEGIN RSA PRIVATE KEY----')

    @integration_test()
    def test_execute_with_ssh_dsa_private_key(self):
        """Testing SecretScannerTool.execute with SSH (DSA) Private Key"""
        self._run_token_test('----BEGIN DSA PRIVATE KEY----')

    @integration_test()
    def test_execute_with_ssh_ec_private_key(self):
        """Testing SecretScannerTool.execute with SSH (EC) Private Key"""
        self._run_token_test('----BEGIN EC PRIVATE KEY----')

    @integration_test()
    def test_execute_with_openssh_private_key(self):
        """Testing SecretScannerTool.execute with OPENSSH Private Key
        """
        self._run_token_test('----BEGIN OPENSSH PRIVATE KEY----')

    @integration_test()
    def test_execute_with_slack_token_xoxa(self):
        """Testing SecretScannerTool.execute with Slack Token (xoxa-2-...)
        """
        self._run_token_test(
            'xoxa-2-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345')
        self._run_token_test(
            'Zxoxa-2-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345',
            match=False)

    @integration_test()
    def test_execute_with_slack_token_xoxb(self):
        """Testing SecretScannerTool.execute with Slack Token (xoxb...)
        """
        self._run_token_test(
            'xoxb-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345')
        self._run_token_test(
            'Zxoxb-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345',
            match=False)

    @integration_test()
    def test_execute_with_slack_token_xoxo(self):
        """Testing SecretScannerTool.execute with Slack Token (xoxo...)
        """
        self._run_token_test(
            'xoxo-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345')
        self._run_token_test(
            'Zxoxo-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345',
            match=False)

    @integration_test()
    def test_execute_with_slack_token_xoxp(self):
        """Testing SecretScannerTool.execute with Slack Token (xoxp...)
        """
        self._run_token_test(
            'xoxp-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345')

        self._run_token_test(
            'Zxoxp-12345678901-12345678901-1234567890123-'
            'abcdefghijklmnopqrstuvwxyz123456',
            match=False)

    @integration_test()
    def test_execute_with_slack_token_xoxr(self):
        """Testing SecretScannerTool.execute with Slack Token (xoxr...)
        """
        self._run_token_test(
            'xoxr-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345')

        self._run_token_test(
            'Zxoxr-123456789012-123456789012-123456789012-'
            'abcdefghijklmnopqrstuvwxyz012345',
            match=False)

    @integration_test()
    def test_execute_with_slack_webhook_url(self):
        """Testing SecretScannerTool.execute with Slack WebHook URL"""
        self._run_token_test(
            'https://hooks.slack.com/services/TABCDEFGH/BACDEFGH/abcdEFGHijkl')

        self._run_token_test(
            'https://hooks.slack.com/workflows/TABCDEFGH/BACDEFGH/abcdEFGHijk')

        self._run_token_test(
            'http://hooks.slack.com/workflows/TABCDEFGH/BACDEFGH/abcdEFGHijk')

    @integration_test()
    def test_execute_with_stripe_live_api_key(self):
        """Testing SecretScannerTool.execute with Stripe API key
        (sk_live_...)
        """
        self._run_token_test('sk_live_abcdEFGH1234ZYXWzyxw6789')
        self._run_token_test('Zsk_live_abcdEFGH1234ZYXWzyxw6789',
                             match=False)

    @integration_test()
    def test_execute_with_stripe_test_api_key(self):
        """Testing SecretScannerTool.execute with Stripe API key
        (sk_test_...)
        """
        self._run_token_test('sk_test_abcdEFGH1234ZYXWzyxw6789')
        self._run_token_test('Zsk_test_abcdEFGH1234ZYXWzyxw6789',
                             match=False)

    @integration_test()
    def test_execute_with_twilio_account_sid(self):
        """Testing SecretScannerTool.execute with Twilio Account SID"""
        self._run_token_test('ACabcdef1234567890abcdef1234567890')
        self._run_token_test('ZACabcdef1234567890abcdef1234567890',
                             match=False)
        self._run_token_test('ACabcdef1234567890abcdef1234567890Z',
                             match=False)

    @integration_test()
    def test_execute_with_twilio_api_key(self):
        """Testing SecretScannerTool.execute with Twilio API Key"""
        self._run_token_test('SKabcdef1234567890abcdef1234567890')
        self._run_token_test('ZSKabcdef1234567890abcdef1234567890',
                             match=False)
        self._run_token_test('SKabcdef1234567890abcdef1234567890Z',
                             match=False)

    @integration_test()
    def test_execute_with_twitter_oauth(self):
        """Testing SecretScannerTool.execute with Twitter OAuth Token"""
        # Lower bounds of length.
        self._run_token_test(
            'TWITTER_OAUTH_TOKEN=1234567890ABCDEFGabcdefg12345XYZxyz')

        # Upper bounds of length.
        self._run_token_test(
            'TWITTER_OAUTH_TOKEN=1234567890ABCDEFGabcdefg12345XYZxyz12345ABcd')

    @integration_test()
    def test_execute_with_success(self):
        """Testing SecretScannerTool.execute with successful result"""
        self._run_token_test('', match=False)

    def _run_token_test(self, token, match=True):
        """Run an execution test with a given token.

        Args:
            token (unicode):
                The token to test for.

            match (bool, optional):
                Whether this should expect a token match.

        Raises:
            AssertionError:
                The resulting state didn't match expectations.
        """
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'def func():\n'
                b'    call_api(%s)\n'
                % token.encode('utf-8')
            ))

        if match:
            self.assertEqual(review.comments, [
                {
                    'filediff_id': review_file.id,
                    'first_line': 2,
                    'num_lines': 1,
                    'text': (
                        'This line appears to contain a hard-coded '
                        'credential, which is a potential security risk. '
                        'Please verify this, and revoke the credential if '
                        'needed.\n'
                        '\n'
                        'Column: 14'
                    ),
                    'issue_opened': True,
                    'rich_text': False,
                },
            ])
        else:
            self.assertEqual(review.comments, [])

        self.assertSpyNotCalled(execute)
