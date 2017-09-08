from lxml import html
import requests


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


teams = {"g2": 5995, "fnatic": 4991, "cloud9": 5752, "mousesports": 4494,
         "gambit": 6651, "misfits": 7557, "envyus": 5991, "heroic": 7175,
         "immortals": 7010}

for teams, uuid in teams.items():
    match_links = getMatch(str(uuid), "https://www.hltv.org/results?team=")
    print("Replays for " + teams + ": ")
    for match in match_links[:10]:
        fixed_match_url = "https://www.hltv.org" + match
        demo_link_results = getDemoLink(fixed_match_url)
        if str(demo_link_results) != "None":
            print("https://www.hltv.org" + str(demo_link_results))
