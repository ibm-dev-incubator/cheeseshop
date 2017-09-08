from lxml import html
import requests
import argparse
import os
import rarfile
import datetime


def get_match(team_id, url):
    """ Get matches based on the URL and Team ID. This returns the match results
        link.
    """
    fixed_team_url = "{}{}".format(url, team_id)
    page = requests.get(fixed_team_url)
    tree = html.fromstring(page.content)
    match_links = tree.xpath('//a[contains(@href, "/matches/")]/@href')
    return match_links


def get_demo_link(url):
    """ Get demo links to download the replays. This returns the download link
        for the demo files.
    """
    page = requests.get(url)
    tree = html.fromstring(page.content)
    demo_links = tree.xpath('//a[contains(@href, "/download/demo")]/@href')
    return demo_links[0] if demo_links else None


def download_replay(demo_url, match_url):
    """ Download replays to ../replays so that we can stage for unraring """
    local_dir = "../replays/"
    local_filename = "{}{}".format(match_url.split('/')[-1], ".rar")
    local_filename_location = "{}{}".format(local_dir, local_filename)
    r = requests.get(demo_url)
    with open(local_filename_location, "wb") as replay:
        replay.write(r.content)
    print("{}{}".format(local_filename, " has finished downloading."))
    return


def format_url(match, base_url="https://www.hltv.org"):
    """ Formats the URL based on the base_url and match path. """
    formatted_url = '{}/{}'.format(base_url, match)
    return formatted_url


def dupe_check_replays(filename):
    """ Check if file exists so that we can skip download if needed. """
    replay_file = "{}{}".format(filename, ".rar")
    if os.path.isfile("{}{}".format("../replays/", replay_file)):
        file_exists = True
    else:
        file_exists = False
    return file_exists


def get_match_date(url):
    match_page = requests.get(url)
    match_tree = html.fromstring(match_page.content)
    match_date = match_tree.xpath('//div[@class="date"]/@data-unix')
    match_timestamp = datetime.datetime.fromtimestamp(
        int(match_date[0]) / 1000.0).strftime('%Y-%m-%d')
    return match_timestamp


def extract_replays():
    for rar in os.listdir("../replays/"):
        if rar.endswith(".rar"):
            filepath = "{}{}".format("../replays/", rar)
            opened_rar = rarfile.RarFile(filepath)
            list_of_files = []
            for replay_file in opened_rar.infolist():
                if os.path.isfile("{}{}".format("../replays/",
                                                replay_file.filename)):
                    print("{}{}".format(replay_file.filename,
                                        " already extracted, skipping."))
                else:
                    list_of_files.append(replay_file.filename)
            for dem in list_of_files:
                print("{}{}".format("Extracting ", dem))
                opened_rar.extract(member=dem, path="../replays/")
    return


def main():
    parser = argparse.ArgumentParser(description='hltv scraper')
    parser.add_argument('--team', required=True,
                        help='Enter in team UUID.')
    parser.add_argument('--list', action='store_true',
                        help='Lists matches.')
    parser.add_argument('--download',
                        action='store_true', help='Downloads locally')
    parser.add_argument('--count', type=int, default=1,
                        help='Number of replays to download.')
    parser.add_argument('--extract', action='store_true',
                        help='Extracts Replays.')
    parser.add_argument('--upload', action='store_true',
                        help="Uploads replay files.")
    args = parser.parse_args()

    replay_count = args.count
    team = args.team
    results_url = "https://www.hltv.org/results?team="
    base_url = "https://www.hltv.org"

    if args.list:
        match_links = get_match(team, results_url)
        for match in match_links[:replay_count]:
            demo_link_results = get_demo_link(format_url(match))
            if demo_link_results:
                match_meta = [match.split('/')[-1],
                              get_match_date(format_url(match)),
                              "{}{}".format(base_url, demo_link_results)]
                match_meta = [get_match_date(format_url(match)),
                              "{}{}".format(base_url, demo_link_results),
                              match.split('/')[-1]]
                print(match_meta)

    if args.download:
        match_url = get_match(team, results_url)
        if not os.path.exists("../replays"):
            os.makedirs("../replays")
        for match in match_url[:replay_count]:
            match_filename = match.split('/')[-1]
            if dupe_check_replays(match_filename):
                print("{}{}".format(match_filename,
                      " has already been downloaded, skipping."))
            else:
                demo_url = get_demo_link(format_url(match))
                if demo_url:
                    print("{}{}{}".format("Downloading ", match_filename,
                                          "..."))
                    download_replay(("{}{}".format(base_url, demo_url)),
                                    format_url(match))

    if args.extract:
        extract_replays()
