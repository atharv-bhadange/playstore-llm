import requests
from bs4 import BeautifulSoup
import json

# Function to scrape game data from Google Play Store
def scrape_google_play_games(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    games = []

    for a in soup.find_all('a', class_='Si6A0c ZD8Cqc'):
        game_name = a.find('div', class_='Epkrse').text
        package_name = a['href'].split('=')[-1]
        icon_url = a.find('img')['src']
        game_url = 'https://play.google.com' + a['href']

        # visit the game page to get the description
        game_page = requests.get(game_url, headers=headers)
        game_soup = BeautifulSoup(game_page.content, 'html.parser')
        tags = game_soup.find_all('a', class_='WpHeLc VfPpkd-mRLv6 VfPpkd-RLmnJb')
        tag_list = []
        for tag in tags:
            if tag.get('aria-label') != "See more details on data safety":
                tag_list.append(tag.get('aria-label'))

        game_description_div = game_soup.find('div', class_='bARER')
        description = ""
        if game_description_div is not None:
            game_description = game_description_div.text
            description = game_description.replace('\n', ' ').replace('\r', '')

        game = {
            "name": game_name,
            "package_name": package_name,
            "tag_list": tag_list,
            "description": description,
            "icon_url": icon_url,
            "game_url": game_url
        }
        games.append(game)

    return games

# URL of Google Play Games
url = 'https://play.google.com/store/apps/collection/promotion_300201f_top_selling_free_games?hl=en_IN&gl=US'

# Scrape the game data
games_data = scrape_google_play_games(url)

# add key to all the data "games"
games_data = {"games": games_data}

with open('game_data.json', 'w') as f:
    json.dump(games_data, f, indent=4)

print("Data scraped and saved to game_data.json")
