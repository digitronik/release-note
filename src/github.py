# Github project data
import re
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from operator import attrgetter

import requests

API_ENDPOINT = "https://api.github.com"
ReleaseTag = namedtuple("ReleaseTag", ["tag", "create_at"])
PR = namedtuple("PR", ["number", "link", "title", "desc", "user_login", "user_link", "labels"])


class GitHub:
    def __init__(self, org, project, api_endpoint=None):
        self.org = org
        self.project = project
        self.api_endpoint = api_endpoint or API_ENDPOINT

    @property
    def release_url(self):
        return f"{self.api_endpoint}/repos/{self.org}/{self.project}/releases"

    @property
    def search_url(self):
        return f"{self.api_endpoint}/search/issues?q=repo:{self.org}/{self.project}+is:pr"

    def call_api(self, apicall, **kwargs):
        data = kwargs.get("data", [])
        data_key = kwargs.get("data_key")

        resp = requests.get(apicall)
        _data = resp.json()
        data += _data[data_key] if data_key else _data

        if "next" in resp.links.keys():
            return self.call_api(resp.links["next"]["url"], data=data, data_key=data_key)
        return data

    def last_release(self):
        """Last release data."""
        data = self.call_api(self.release_url)
        if data:
            last_release = data[0]
            tag = last_release["tag_name"]
            created_at = datetime.strptime(last_release["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            created_at = created_at + timedelta(5)  # Add 5 sec offset.
            return ReleaseTag(tag=tag, create_at=created_at)
        else:
            return None

    def merged_prs(self, from_time=None, to_time=None):
        # Grab merged PR data
        prs = []
        to_time = to_time if to_time else datetime.today().replace(microsecond=0)
        if from_time:
            merged_prs_query = (
                f"{self.search_url}+merged:{from_time.isoformat()}..{to_time.isoformat()}"
            )
        else:
            merged_prs_query = f"{self.search_url}+is:merged"

        merged_prs = self.call_api(merged_prs_query, data_key="items")

        for pr in merged_prs:
            description = pr["body"]
            description = "\n".join(
                [l for l in description.split("\n") if not re.match("Signed-off-by", l)]
            )
            prs.append(
                PR(
                    pr["number"],
                    pr["html_url"],
                    pr["title"],
                    description,
                    pr["user"]["login"],
                    pr["user"]["html_url"],
                    [],
                )
            )
        return sorted(prs, key=attrgetter("number"))


if __name__ == "__main__":
    gh = GitHub("foo", "bar")
