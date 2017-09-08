from lxml import html
import requests
import argparse


# Get matches based on the URL + Team ID. This returns match result links.
def get_match(team_id, url):
    fixed_team_url = url + team_id
    page = requests.get(fixed_team_url)
    tree = html.fromstring(page.content)
    match_links = tree.xpath('//a[contains(@href, "/matches/")]/@href')
    return match_links


# Get demo links to download replay.
def get_demo_link(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    demo_links = tree.xpath('//a[contains(@href, "/download/demo")]/@href')
    return demo_links[0] if demo_links else None


def download_replay(demo_url, match_url):
    local_filename = match_url.split('/')[-1]
    r = requests.get(demo_url)
    print(r)
    print(local_filename)


def format_url(match, base_url="https://www.hltv.org"):
    formatted_url = '{}/{}'.format(base_url, match)
    return formatted_url


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

    team = args.team
    results_url = "https://www.hltv.org/results?team="

    if args.list:
        match_links = get_match(team, results_url)
        for match in match_links[:args.count]:
            print(match)

    if args.verbose:
        match_links = get_match(team, results_url)
        for match in match_links[:args.count]:
            demo_link_results = get_demo_link(format_url(match))
            if str(demo_link_results) != "None":
                print(match.split('/')[-1])
                print("https://www.hltv.org" + str(demo_link_results))

#    if args.download:
#        downloadReplay( )
