from lxml import html
import requests
import argparse


# Get matches based on the URL + Team ID. This returns match result links.
def getMatch(team_id, url):
    fixed_team_url = url + team_id
    page = requests.get(fixed_team_url)
    tree = html.fromstring(page.content)
    match_links = tree.xpath('//a[contains(@href, "/matches/")]/@href')
    return match_links


# Get demo links to download replay.
def getDemoLink(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    demo_links = tree.xpath('//a[contains(@href, "/download/demo")]/@href')
    return demo_links[0] if demo_links else None


def downloadReplay(demo_url, match_url):
    local_filename = match_url.split('/')[-1]
    r = requests.get(demo_url)
    print(r)
    print(local_filename)


def formatURL(match, base_url=""):
    if not base_url:
        base_url = "https://www.hltv.org"
    formattedURL = base_url + match
    return formattedURL


def main():
    parser = argparse.ArgumentParser(description='hltv scraper')
    parser.add_argument('--team', type=int, help='Enter in team UUID.')
    parser.add_argument('--list', action='store_true', help='Lists matches.')
    parser.add_argument('--verbose', action='store_true', help='Lists DL.')
    parser.add_argument('--download',
                        action='store_true', help='Downloads locally')
    args = parser.parse_args()

    team = args.team
    results_url = "https://www.hltv.org/results?team="

    if args.list:
        match_links = getMatch(str(team), results_url)
        for match in match_links[:10]:
            print(match)

    if args.verbose:
        match_links = getMatch(str(team), results_url)
        for match in match_links[:10]:
            demo_link_results = getDemoLink(formatURL(match))
            if str(demo_link_results) != "None":
                print(match.split('/')[-1])
                print("https://www.hltv.org" + str(demo_link_results))

#    if args.download:
#        downloadReplay( )
