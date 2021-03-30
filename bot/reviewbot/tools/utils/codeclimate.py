"""Utility functions for processing CodeClimate payloads.

Version Added:
    3.0
"""

from __future__ import unicode_literals


def add_comment_from_codeclimate_issue(issue_payload, review_file):
    """Add a comment to a review from a CodeClimate issue payload.

    Several tools support outputting CodeClimate issue payloads. This function
    parses an issue payload, adding a comment to a review based on the result.

    Args:
        issue_payload (dict):
            The CodeClimate issue payload.

        review_file (reviewbot.processing.review.File):
            The file being reviewed.
    """
    positions = issue_payload['location']['positions']
    begin = positions['begin']
    end = positions['end']
    first_line = begin['line']

    review_file.comment(text=issue_payload['description'],
                        first_line=first_line,
                        num_lines=end['line'] - first_line + 1,
                        start_column=begin['column'],
                        error_code=issue_payload['check_name'])
