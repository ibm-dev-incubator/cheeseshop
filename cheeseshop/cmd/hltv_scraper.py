from lxml import html
import requests
import argparse
import os


def get_match(team_id, url):
    """ Get matches based on the URL + Team ID. This returns the match results
        link.
    """
    fixed_team_url = url + team_id
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
    local_dir = "../replays/"
    local_filename = (match_url.split('/')[-1] + ".rar")
    local_filename_location = (local_dir + local_filename)
    r = requests.get(demo_url)
    with open(local_filename_location, "wb") as replay:
        replay.write(r.content)
    print(local_filename + " has finished downloading.")
    return


def format_url(match, base_url="https://www.hltv.org"):
    """ Formats the URL based on the base_url + match path. """
    formatted_url = '{}/{}'.format(base_url, match)
    return formatted_url


def dupe_check_replays(filename):
    replay_file = filename + ".rar"
    if os.path.isfile("../replays/" + replay_file):
        file_exists = True
    else:
        file_exists = False
    return file_exists


def main():
    parser = argparse.ArgumentParser(description='hltv scraper')
    parser.add_argument('--team', help='Enter in team UUID.')
    parser.add_argument('--list', action='store_true', help='Lists matches.')
    parser.add_argument('--verbose', action='store_true', help='Lists DL.')
    parser.add_argument('--download',
                        action='store_true', help='Downloads locally')
    parser.add_argument('--count', type=int, default=1,
                        help='Number of replays to download.')
    args = parser.parse_args()

    replay_count = args.count + 1
    team = args.team
    results_url = "https://www.hltv.org/results?team="
    base_url = "https://www.hltv.org"

    if args.list:
        match_links = get_match(team, results_url)
        for match in match_links[:replay_count]:
            print(match)

    if args.verbose:
        match_links = get_match(team, results_url)
        for match in match_links[:replay_count]:
            demo_link_results = get_demo_link(format_url(match))
            if demo_link_results:
                print(match.split('/')[-1])
                print("https://www.hltv.org" + str(demo_link_results))

    if args.download:
        match_url = get_match(team, results_url)
        for match in match_url[:replay_count]:
            if dupe_check_replays(match):
                print(match + " has already been downloaded, skipping.")
            else:
                demo_url = get_demo_link(format_url(match))
                if demo_url:
                    download_replay((base_url + demo_url),
                                    format_url(match))
