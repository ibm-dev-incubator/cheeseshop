from lxml import html
import requests
import argparse
import os
import rarfile
import datetime


results_url = "https://www.hltv.org/results?team="
base_url = "https://www.hltv.org"


class Scraper:
    def __init__(self, output_dir, team, replays,
                 _list=False, _download=False, extract=False):
        self.directory = output_dir
        self.team = team
        self.replay_count = replays
        self.replay_list = _list
        self.download = _download
        self.extract = extract
        self.matches = []
        if self.download or self.replay_list:
            self.matches = self.get_match(self.team)[:self.replay_count]

    def run(self):
        for match in self.matches:
            if self.replay_list:
                self._list(match)

            if self.download:
                self._download(match)

        if self.extract:
            self.extract_replays()

    def _download(self, match):
        match_filename = match.split('/')[-1]
        if self.dupe_check_replays(match_filename):
            print("{} has already been downloaded,"
                  "skipping.".format(match_filename))
        else:
            demo_url = self.get_demo_link(self.format_url(match))
            if demo_url:
                print("Downloading {}...".format(match_filename,))
                self.download_replay(("{}{}".format(base_url, demo_url)),
                                     self.format_url(match))
            else:
                print("Skipping Download for", match.split('/')[-1],
                      ". Demo file not available yet.")

    def _list(self, match):
        demo_url = self.get_demo_link(self.format_url(match))
        if demo_url:
            match_meta = [self.get_match_date(self.format_url(match)),
                          "{}{}".format(base_url, demo_url),
                          match.split('/')[-1]]
        else:
            match_meta = [self.get_match_date(self.format_url(match)),
                          "No Demo File Yet", match.split('/')[-1]]
        print(match_meta)

    def download_replay(self, demo_url, match_url):
        """ Download replays to ../replays so that we can stage for extracting
        """
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        local_filename = "{}.rar".format(match_url.split('/')[-1])
        local_filename_location = os.path.join(self.directory, local_filename)
        r = requests.get(demo_url)
        with open(local_filename_location, "wb") as replay:
            replay.write(r.content)
        print("{} has finished download.".format(local_filename))

    def dupe_check_replays(self, filename):
        """ Check if file exists so that we can skip download if needed. """
        replay_file = "{}.rar".format(filename)
        return os.path.isfile(os.path.join(self.directory, replay_file))

    def extract_replays(self):
        """ Extract all .rar files in the specified directory. Skip files that
            have already been extracted.
        """
        for rar in os.listdir(self.directory):
            if not rar.endswith('.rar'):
                continue
            filepath = os.path.join(self.directory, rar)
            opened_rar = rarfile.RarFile(filepath)
            for replay_file in opened_rar.infolist():
                if os.path.isfile(os.path.join(self.directory,
                                  replay_file.filename)):
                    print("{} already extracted, skipping.".format(
                          replay_file.filename))
                else:
                    print("Extracting {}.".format(replay_file.filename))
                    opened_rar.extract(member=replay_file,
                                       path=self.directory)

    def format_url(self, match, base_url="https://www.hltv.org"):
        """ Formats the URL based on the base_url and match path. """
        formatted_url = '{}/{}'.format(base_url, match)
        return formatted_url

    def get_demo_link(self, url):
        """ Get demo links to download the replays. This returns the download
            link for the demo files.
        """
        page = requests.get(url)
        tree = html.fromstring(page.content)
        demo_links = tree.xpath('//a[contains(@href, "/download/demo")]/@href')
        return demo_links[0] if demo_links else None

    def get_match(self, team_id):
        """ Get matches based on the URL and Team ID. This returns the match
            results link.
        """
        fixed_team_url = "{}{}".format(results_url, team_id)
        page = requests.get(fixed_team_url)
        tree = html.fromstring(page.content)
        match_links = tree.xpath('//a[contains(@href, "/matches/")]/@href')
        return match_links

    def get_match_date(self, url):
        """ Get Unix timestamp from a specific match and convert it to readable
            date.
        """
        match_page = requests.get(url)
        match_tree = html.fromstring(match_page.content)
        match_date = match_tree.xpath('//div[@class="date"]/@data-unix')
        match_timestamp = datetime.datetime.fromtimestamp(
            int(match_date[0]) / 1000.0).strftime('%Y-%m-%d')
        return match_timestamp


def main():
    parser = argparse.ArgumentParser(description='hltv scraper')
    parser.add_argument('--download', action='store_true',
                        help='Download replay files.')
    parser.add_argument('--extract', action='store_true',
                        help='Extract replay files.')
    parser.add_argument('--list', action='store_true',
                        help='List match details.')
    parser.add_argument('--directory', action="store", default="../replays/",
                        help='Specify custom output directory to store replay'
                             ' files. Can also be used with --extract when'
                             ' extracting already downloaded replays.')
    parser.add_argument('--replays', type=int, default=1,
                        help='Number of replays to download.')
    parser.add_argument('--team',
                        help='Team UUID for hltv.org.')
    args = parser.parse_args()
    if not (args.team or args.extract):
        parser.error('Please use --team to specify the team, or --extract if '
                     'extracting from directory.')

    team = args.team

    scraper = Scraper(args.directory, team, args.replays, args.list,
                      args.download, args.extract)
    scraper.run()
