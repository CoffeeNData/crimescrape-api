import argparse
import concurrent.futures
import json
import logging.handlers
import os
import re
import threading
import time
from hashlib import md5

from flask import Flask, jsonify
from markupsafe import escape

from sources.cib import CIBSearch
from sources.database import DatabaseSearch
from sources.europol import EuropolSearch
from sources.fbi import FBISearch
from sources.guardiacivil import GuardiaCivilSearch
from sources.interpol import InterpolSearch
from sources.nca import NCASearch
from sources.newsouthwalespolice import NewSouthWalesPoliceSearch
from sources.ofac import OFACSearch
from sources.ofsi import OFSISearch
from sources.opensanctions import OpenSanctionsSearch
from sources.policianacional import PoliciaNacionalSearch
from sources.politie import PolitieSearch
from sources.ussecretservice import SecretServiceSearch

# Parse command-line arguments for headless, port, and host options
parser = argparse.ArgumentParser(description="CrimeScrape API Server")
parser.add_argument(
    "--headless", action="store_true", help="Run searches in headless mode"
)
parser.add_argument(
    "--port",
    type=int,
    default=5000,
    help="Port to run the API server on. Only for API mode",
)
parser.add_argument(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Bind address for the API server. Only for API mode",
)
parser.add_argument(
    "--threads", type=int, default=5, help="Maximum number of threads to use per search"
)
parser.add_argument(
    "--nocache", action="store_true", help="Disable caching the responses"
)
parser.add_argument(
    "--timeout",
    type=int,
    default=30,
    help="Timeout in seconds for each individual thread",
)
parser.add_argument(
    "--api",
    "--run-as-api",
    action="store_true",
    help="Run in API mode",
)
parser.add_argument("-q", "--query", type=str, help="JSON file containing the query")
parser.add_argument("-r", "--results", type=str, help="Path to store the query results")
parser.add_argument(
    "-l",
    "--logs",
    type=str,
    default="crimescrape.log",
    help="Name for the logfile. Default = crimescrape.log",
)
args = parser.parse_args()

app = Flask(__name__)
CACHE_DIR = "cache"
CACHE_MAX_DAYS = 5
EMAIL_REGEX = r"^\S+@\S+\.\S+$"
PHONE_REGEX = r"^\+?[(]?\d{3})?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$"
IP_REGEX = r"^((\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])$"
HOST_REGEX = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
HEADLESS = args.headless  # default false
MAX_THREADS = args.threads  # default 5
USE_CACHE = not args.nocache
TIMEOUT = args.timeout
STANDALONE = False if args.api else True  # Runs standalone by default

# Initialize logger early for use in module-level functions
logger = None

# Define sources for both standalone and API mode
def get_name_sources():
    return [
        InterpolSearch(logging=logger, headless=HEADLESS),
        EuropolSearch(logging=logger, headless=HEADLESS),
        NCASearch(logging=logger, headless=HEADLESS),
        FBISearch(logging=logger, headless=HEADLESS),
        PolitieSearch(logging=logger, headless=HEADLESS),
        OFACSearch(logging=logger, headless=HEADLESS),
        SecretServiceSearch(logging=logger),
        PoliciaNacionalSearch(logging=logger),
        GuardiaCivilSearch(logging=logger),
        DatabaseSearch(logging=logger, db_path="db/local.db"),
        CIBSearch(logging=logger),
        NewSouthWalesPoliceSearch(logging=logger),
        OFSISearch(logging=logger),
        OpenSanctionsSearch(logging=logger),
    ]


CURRENTLY_RUNNING = []  # DO NOT CHANGE


class RunningSearches:
    """Thread-safe tools for the management of active searches"""

    _lock = threading.Lock()

    @staticmethod
    def add_running(search_item) -> None:
        """
        Adds a new search item to RUNNING_SEARCHES.
        """
        global CURRENTLY_RUNNING
        with RunningSearches._lock:
            CURRENTLY_RUNNING.append(search_item)

    @staticmethod
    def remove_running(search_item) -> None:
        """
        Removes a search item from RUNNING_SEARCHES.
        """
        global CURRENTLY_RUNNING
        with RunningSearches._lock:
            CURRENTLY_RUNNING.remove(search_item)

    @staticmethod
    def is_running(search_item) -> bool:
        """
        Checks if search_item exists in RUNNING_SEARCHES.
        Returns True if found, False otherwise.
        """
        global CURRENTLY_RUNNING
        with RunningSearches._lock:
            return search_item in CURRENTLY_RUNNING


def store_cache(filename: str, data: list[dict]) -> bool:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, filename)

    try:
        cache_data = {
            "timestamp": int(time.time()),
            "data": data,
        }
        with open(cache_path, "w") as file:
            file.write(json.dumps(cache_data, ensure_ascii=False))

        logger.info(f"Stored cache {filename}")
        return True
    except IOError as e:
        logger.error(f"Failed to store cache {filename}: {e}")
    return False


def load_cache(filename: str) -> list[dict] | None:
    cache_path = os.path.join(CACHE_DIR, filename)
    try:
        with open(cache_path, "r") as file:
            cache = json.loads(file.read())
            timestamp = cache["timestamp"]  # Load the timestamp
            data = cache["data"]

            # Check if the cache is stale
            days_since = int((time.time() - timestamp) / 86400)  # Seconds
            if days_since > CACHE_MAX_DAYS:
                os.remove(cache_path)  # Delete the cachefile
                return None
            else:
                return data

    except Exception as e:
        logger.error(f"Error loading cache {filename}: {e}")
        return None


def gen_cache_filename(content: str) -> str:
    """Generate a UID-like filename for cache. For names, it should be (fname+lname). For other, just the plain string.

    Args:
        content (str): The query to generate the filename from.

    Returns:
        str: The resulting filename for cache I/O operations.
    """
    res = md5(content.upper().encode()).hexdigest()
    return res


def gen_results(status: str, data: list[dict]) -> dict:
    status_list = ["fresh", "cached", "error"]
    if status not in status_list:
        logger.error("API response with unrecognised status")
        return {"status": "error"}
    return {"status": status, "data": data}


def gen_error(info: str):
    logger.error(f"Error: {info}")
    return {"status": "error", "info": info}



def execute_search(sources, search_methods, results, max_threads, timeout):
    """Execute searches across multiple threads"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_tasks = {
            executor.submit(method, src): (src, method)
            for src in sources
            for method in search_methods
        }

        done, not_done = concurrent.futures.wait(
            future_tasks.keys(),
            timeout=timeout,
            return_when=concurrent.futures.ALL_COMPLETED,
        )

        # Process completed searches
        for future in done:
            source, method = future_tasks[future]
            try:
                result = future.result()
                if result:
                    logger.debug(f"Results found for {source}: {result}")
                    results.append(result)
            except Exception as e:
                logger.error(f"Error searching {source} with {method}: {e}")

        # Handle timeouts
        for future in not_done:
            source, method = future_tasks[future]
            logger.warning(f"Search for {source} using {method} timed out.")
            future.cancel()


def perform_search(
        query: str, cache_type: str, sources, search_methods, log_message: str
):
    """
    Perform a generic search given a query identifier, sources, and search methods.

    Args:
        query (str): Unique identifier for the search (e.g., SSN or concatenated name).
        sources (list): List of source objects to perform searches.
        search_methods (list): List of search methods (functions).
        log_message (str): Log message describing the search context.
        cache_type (str): Type of the cache to use.

    Returns:
        Response: JSON response containing cached or fresh results.
    """
    query = escape(query)
    results: list[dict] = []
    query_id = gen_cache_filename(cache_type + query)

    logger.info(log_message)

    # Check if search is already running
    while RunningSearches.is_running(query_id):
        time.sleep(0.1)
    RunningSearches.add_running(query_id)

    # Try to load cache
    if USE_CACHE:
        cache = load_cache(query_id)
        if cache:
            RunningSearches.remove_running(query_id)
            logger.info(f"Cache found: {query_id}")
            return jsonify(gen_results("cached", cache))

    # Execute search
    execute_search(sources, search_methods, results, MAX_THREADS, TIMEOUT)

    # Cache and return results
    if USE_CACHE:
        store_cache(query_id, results)

    RunningSearches.remove_running(query_id)

    if STANDALONE:
        return gen_results("fresh", results)
    return jsonify(gen_results("fresh", results))


@app.route("/api/searchHost/<host>")
def search_by_host(host: str):
    # Validate input
    if not (re.match(IP_REGEX, host) or re.match(HOST_REGEX, host)):
        return gen_error("Invalid hostname")

    sources = []
    search_methods = []
    return perform_search(
        query=host,
        cache_type="host",
        sources=sources,
        search_methods=search_methods,
        log_message=f"Starting host search for: {host}",
    )


@app.route("/api/searchPhone/<phone>")
def search_by_phone(phone: str):
    if not re.match(PHONE_REGEX, phone):
        return gen_error("Invalid phone number")

    sources = []
    search_methods = []
    return perform_search(
        query=phone,  # TODO: Needs input standarization before being passed to the caching system
        cache_type="phone",
        sources=sources,
        search_methods=search_methods,
        log_message=f"Starting phone search for: {phone}",
    )


@app.route("/api/searchEmail/<email>")
def search_by_email(email: str):
    if not re.match(EMAIL_REGEX, email):
        return gen_error("Invalid email address")

    sources = []
    search_methods = []
    return perform_search(
        query=email,
        cache_type="email",
        sources=sources,
        search_methods=search_methods,
        log_message=f"Starting email search for: {email}",
    )


"""
SSNs and names can not be easily verified since there is no possible regex to
match all of the possibilities.
"""


@app.route("/api/searchSSN/<ssn>")
def search_by_ssn(ssn: str):
    sources = []
    search_methods = []
    return perform_search(
        query=ssn,
        cache_type="ssn",
        sources=sources,
        search_methods=search_methods,
        log_message=f"Starting SSN search for: {ssn}",
    )


@app.route("/api/search/<fname>/<lname>")
def search_by_name(fname: str, lname: str):
    sources = get_name_sources()

    search_methods = [
        lambda src: src.search(fname, lname),
    ]

    return perform_search(
        query=fname + lname,
        cache_type="name",
        sources=sources,
        search_methods=search_methods,
        log_message=f"Starting name search for subject: {fname} {lname}",
    )


def run_standalone(queryfile: str, resultfile: str) -> str | None:
    """Run the searches in standalone mode.

    Args:
        queryfile (str): The path to the file containing the query to be searched.
        resultfile (str): The filename or path to store the found results.

    Returns:
        str | None: The full path of the results can be returned. Useful when only a filename has been supplied.
    """

    if os.path.exists(resultfile):
        os.remove(resultfile)

    search_engines = get_name_sources()
    with open(queryfile, "r", encoding="UTF-8") as f:
        search_query = json.load(f)

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_engine = {
            executor.submit(
                engine.search,
                search_query["fname"],
                search_query["lname"],  # need add for every function timeout argument
            ): engine.__class__.__name__
            for engine in search_engines
        }
        for future in concurrent.futures.as_completed(future_to_engine):
            engine_name = future_to_engine[future]
            try:
                logger.info(f"Success: executed module -> {engine_name}")
                result = future.result()
                if result:  # Only store non-empty results
                    results[engine_name] = result
            except Exception as err:
                logger.warning(f"Failed: execute module -> {engine_name} as error {err}")
                continue

    if results:
        with open(resultfile, "w") as f:
            json.dump(results, f, indent=4, sort_keys=True)
        logger.info(f"Found results {results} on {search_query}")
        return os.path.abspath(resultfile)
    else:
        logger.info("No results found.")
        return None


if __name__ == "__main__":

    # Set logging up here to avoid race conditions
    if os.path.exists(args.logs):
        os.remove(args.logs)
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=args.logs, encoding="utf-8", level=logging.INFO)

    # Decide and start appropriate mode
    if STANDALONE:
        # Make sure the arguments were correctly passed
        if not (args.query or args.results):
            print("Error: --query/--results file required for standalone mode.")
            exit(1)

        run_standalone(args.query, args.results)
    else:
        app.run(host=args.host, port=args.port)
