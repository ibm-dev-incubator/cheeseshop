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


# List Matches for the team.
def listMatches(team):
    pass


def main():
    parser = argparse.ArgumentParser(description='hltv scraper')
    parser.add_argument('--team', type=int, help='Enter in team UUID.')
    parser.add_argument('--list', action='store_true', help='Lists matches.')
    parser.add_argument('--download', action='store_true', help='Lists DL.')
    args = parser.parse_args()

    team = args.team
    if args.list:
        match_links = getMatch(str(team), "https://www.hltv.org/results?team=")
        for match in match_links[:10]:
            print(match)

    if args.download:
        match_links = getMatch(str(team), "https://www.hltv.org/results?team=")
        for match in match_links[:10]:
            fixed_match_url = "https://www.hltv.org" + match
            demo_link_results = getDemoLink(fixed_match_url)
            if str(demo_link_results) != "None":
                print(match.split('/')[-1])
                print("https://www.hltv.org" + str(demo_link_results))
