#!/usr/bin/env python

import os
import uuid
import json
from datetime import time, date, datetime, timedelta
from random import randint, choice
import random
import click
import git
import logging
import holidays

HELLO_WORLD_CPP = """#include <iostream>\nint main()\n{\n  std::cout << \"Hello World!\" << std::endl;\n  return 0;\n}\n"""

DEFAULT_FILE_NAME = 'main.cpp'
DEFAULT_MESSAGES_FILE = 'commit-messages.json'

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class RockStar:
    def __init__(self, days=400, days_off=(), file_name=DEFAULT_FILE_NAME,
                 code=HELLO_WORLD_CPP, off_fraction=0.0, repo_path=None, messages_file_path=None, use_existing_repo=False, holiday_country='US'):
        self.days = days
        self.file_name = file_name
        self.code = code
        self.days_off = list(map(str.capitalize, days_off))
        self.off_fraction = off_fraction
        self.repo_path = repo_path or os.getcwd()
        self.file_path = os.path.join(self.repo_path, file_name)
        self.messages_file_path = messages_file_path or os.path.join(self.repo_path, DEFAULT_MESSAGES_FILE)
        self.repo = None
        self.use_existing_repo = use_existing_repo
        self.holiday_country = holiday_country
        self._load_commit_messages()

    def _load_commit_messages(self):
        try:
            with open(self.messages_file_path) as f:
                messages_file_contents = json.load(f)
            names = messages_file_contents['names']
            messages = messages_file_contents['messages']
            self.commit_messages = [m.format(name=choice(names)) for m in messages]
        except Exception as e:
            logging.error(f"Failed to load commit messages: {e}")
            self.commit_messages = ["Update {name}"]

    def _get_random_commit_message(self):
        return choice(self.commit_messages)

    def _make_last_commit(self):
        try:
            with open(self.file_path, 'w') as f:
                f.write(self.code)
            os.environ['GIT_AUTHOR_DATE'] = ''
            os.environ['GIT_COMMITTER_DATE'] = ''
            self.repo.index.add([self.file_path])
            self.repo.index.commit('Final commit :sunglasses:')
        except Exception as e:
            logging.error(f"Failed to make last commit: {e}")
        finally:
            self._reset_git_env_dates()

    def _edit_and_commit(self, message, commit_date):
        try:
            with open(self.file_path, 'w') as f:
                f.write(message)
            self.repo.index.add([self.file_path])
            date_in_iso = commit_date.strftime("%Y-%m-%d %H:%M:%S")
            os.environ['GIT_AUTHOR_DATE'] = date_in_iso
            os.environ['GIT_COMMITTER_DATE'] = date_in_iso
            self.repo.index.commit(self._get_random_commit_message())
        except Exception as e:
            logging.error(f"Failed to commit on {commit_date}: {e}")
        finally:
            self._reset_git_env_dates()

    @staticmethod
    def _reset_git_env_dates():
        os.environ['GIT_AUTHOR_DATE'] = ''
        os.environ['GIT_COMMITTER_DATE'] = ''

    @staticmethod
    def _get_random_time():
        return time(hour=randint(4, 18), minute=randint(0, 59),
                    second=randint(0, 59), microsecond=randint(0, 999999))

    def _get_dates_list(self):
        today = date.today()
        delta = self.days
        dates = []
        # Setup holidays
        if self.holiday_country.lower() == 'world':
            all_holidays = set()
            for country in holidays.list_supported_countries():
                try:
                    all_holidays.update(holidays.country_holidays(country, years=today.year))
                except Exception:
                    continue
        else:
            try:
                all_holidays = set(holidays.country_holidays(self.holiday_country, years=today.year))
            except Exception:
                all_holidays = set()
        for i in range(delta):
            day = today - timedelta(days=delta - i)
            if day.strftime('%A') in self.days_off:
                continue
            if day in all_holidays:
                continue
            if randint(1, 100) < self.off_fraction * 100:
                continue
            for _ in range(randint(1, 5)):
                dates.append(datetime.combine(day, self._get_random_time()))
        return dates

    def make_me_a_rockstar(self):
        try:
            if self.use_existing_repo and os.path.exists(os.path.join(self.repo_path, '.git')):
                self.repo = git.Repo(self.repo_path)
                logging.info(f"Using existing git repository at {self.repo_path}")
            else:
                self.repo = git.Repo.init(self.repo_path)
                logging.info(f"Initialized new git repository at {self.repo_path}")
        except Exception as e:
            logging.error(f"Failed to initialize or open git repository: {e}")
            return
        label = 'Making you a Rockstar Programmer'
        try:
            with click.progressbar(self._get_dates_list(), label=label) as bar:
                for commit_date in bar:
                    self._edit_and_commit(str(uuid.uuid1()), commit_date)
            self._make_last_commit()
            logging.info('You are now a Rockstar Programmer!')
        except Exception as e:
            logging.error(f"Error during commit process: {e}")

@click.command()
@click.option('--days', type=int, default=100, help='Number of days to generate commits for')
@click.option('--days-off', multiple=True, default=(), help='Days of the week to skip (e.g., Sunday, Saturday)')
@click.option('--file-name', type=str, default=DEFAULT_FILE_NAME, help='File to commit to')
@click.option('--code', type=str, default=HELLO_WORLD_CPP, help='Code to write in the file')
@click.option('--off-fraction', type=float, default=0.0, help='Fraction of days to randomly skip')
@click.option('--repo-path', type=click.Path(), default=None, help='Path to the git repository')
@click.option('--messages-file-path', type=click.Path(), default=None, help='Path to the commit messages JSON file')
@click.option('--use-existing-repo', is_flag=True, default=False, help='Use existing git repo if present')
@click.option('--holiday-country', type=str, default='US', help='Country code for public holidays (e.g., US, IN, GB, etc. Use "world" to skip all world holidays)')
def cli(days, days_off, file_name, code, off_fraction, repo_path, messages_file_path, use_existing_repo, holiday_country):
    magic = RockStar(
        days=days,
        days_off=days_off,
        file_name=file_name,
        code=code,
        off_fraction=off_fraction,
        repo_path=repo_path,
        messages_file_path=messages_file_path,
        use_existing_repo=use_existing_repo,
        holiday_country=holiday_country
    )
    magic.make_me_a_rockstar()

if __name__ == "__main__":
    cli()