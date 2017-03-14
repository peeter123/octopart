"""
Top-level API, provides access to the Octopart API
without directly instantiating a client object.

Also wraps the response JSON in types that provide easier access
to various fields.
"""

import itertools
from concurrent.futures import ThreadPoolExecutor

from octopart import utils
from octopart.client import OctopartClient
from octopart.models import PartsMatchResult
from octopart.models import PartsSearchResult


MAX_REQUEST_THREADS = 10


def match(mpns,
          sellers=None,
          specs=False,
          imagesets=False,
          descriptions=False):
    """
    Match a list of MPNs against Octopart.

    Args:
        mpns (list): list of str MPNs
        sellers (list, optional): list of str part sellers
        specs (bool, optional): whether to include specs for parts
        imagesets (bool, optional): whether to include imagesets for parts
        descriptions (bool, optional):
            whether to include descriptions for parts

    Returns:
        list of `models.PartsMatchResult` objects.
    """
    client = OctopartClient()
    unique_mpns = utils.unique(mpns)

    # Use free-form query 'q' field to maximize chances of getting a match.
    if sellers is None:
        queries = [
            {
                'q': mpn,
                'reference': mpn
            }
            for mpn in unique_mpns
        ]
    else:
        queries = [
            {
                'q': mpn,
                'seller': seller,
                'reference': mpn,
            }
            for (mpn, seller) in itertools.product(unique_mpns, sellers)
        ]

    def _request_chunk(chunk):
        return client.match(
            queries=chunk,
            specs=specs,
            imagesets=imagesets,
            descriptions=descriptions)

    # Execute API calls concurrently to significantly speed up
    # issuing multiple HTTP requests.
    with ThreadPoolExecutor(max_workers=MAX_REQUEST_THREADS) as pool:
        responses = pool.map(_request_chunk, utils.chunked(queries))

    return [
        PartsMatchResult(result)
        for response in responses
        for result in response['results']
    ]


def search(query,
           start=0,
           limit=10,
           sortby=(),
           filter_fields=None,
           filter_queries=None):
    """
    Search Octopart for a general keyword (and optional filters).

    Args:
        query (str): Free-form keyword query
        start (int, optional): Ordinal position of first result
        limit (int, optional): Maximum number of results to return
        sortby (list, optional): [(fieldname, order)] list of tuples
        filter_fields (dict, optional): {fieldname: value} dict
        filter_queries (dict, optional): {fieldname: value} dict

    Returns:
        list of `models.PartsSearchResult` objects.
    """
    client = OctopartClient()
    response = client.search(
        query,
        start=start,
        limit=limit,
        sortby=sortby,
        filter_fields=filter_fields,
        filter_queries=filter_queries)
    return PartsSearchResult(response)
