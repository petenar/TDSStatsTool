# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 12:56:13 2024

@author: Petr
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json

# Main data structure to store formats, tournaments, and card information
data = {
    "formats": {},
    "cards": {}
}

data2 = {
    "formats": {},
    "cards": {}
    }

# URL to retrieve all formats in tournament results
base_url = "https://digitalgateopen.com/tournament-results-overview"
local_url = "https://digitalgateopen.com/local-results-overview"

# Function to get links for all formats in tournament results
def get_format_links(base_url):
    response = requests.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    format_links = {}
    for link in soup.select(".overlay-cross a"):
        format_name = link.text.strip()
        format_url = link.get('href')
        full_url = format_url if format_url.startswith("http") else f'https://digitalgateopen.com/{format_url}'
        format_links[format_name] = full_url
        
    return format_links

# Function to get links for all formats in local results
def get_local_format_links(local_url):
    response = requests.get(local_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    format_links = {}
    for link in soup.select(".overlay-cross a"):
        format_name = link.text.strip()
        format_url = link.get('href')
        full_url = format_url if format_url.startswith("http") else f'https://digitalgateopen.com/{format_url}'
        format_links[format_name] = full_url
        
    return format_links

# Function to scrape tournaments and decks for a specific format
def get_tournaments_for_format(format_url, format_name):
    response = requests.get(format_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize the format in the data structure if not already present
    data["formats"].setdefault(format_name, {"tournaments": []})
    
    for tournament_block in soup.select(".row"):
        decks = []
        
        for deck_card in tournament_block.select(".column-third.padding-8.padding-side-8"):
            deck_name = deck_card.select_one("a[title]").get("title").strip() if deck_card.select_one("a[title]") else "Unknown Deck"
            link_tag = deck_card.select_one("a")
            deck_link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
            
            if deck_link and not deck_link.startswith('http'):
                deck_link = f'https://digitalgateopen.com/{deck_link}'
            
            decks.append({
                "deck_name": deck_name,
                "deck_link": deck_link
            })
        
        data["formats"][format_name]["tournaments"].append({
            "decks": decks
        })
# Function to scrape tournaments and decks for a specific format
def get_locals_for_format(format_url, format_name):
    response = requests.get(format_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize the format in the data structure if not already present
    data2["formats"].setdefault(format_name, {"tournaments": []})
    
    for tournament_block in soup.select(".row"):
        decks = []
        
        for deck_card in tournament_block.select(".column-third.padding-8.padding-side-8"):
            deck_name = deck_card.select_one("a[title]").get("title").strip() if deck_card.select_one("a[title]") else "Unknown Deck"
            link_tag = deck_card.select_one("a")
            deck_link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
            
            if deck_link and not deck_link.startswith('http'):
                deck_link = f'https://digitalgateopen.com/{deck_link}'
            
            decks.append({
                "deck_name": deck_name,
                "deck_link": deck_link
            })
        
        data2["formats"][format_name]["tournaments"].append({
            "decks": decks
        })     

# Function to scrape each decklist given a deck URL
def scrape_decklist(deck_url):
    response = requests.get(deck_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    decklist = []
    for card in soup.select(".card-group"):
        card_link_tag = card.select_one("a")
        if card_link_tag and 'href' in card_link_tag.attrs:
            card_link = card_link_tag['href']
            card_ref_code = card_link.split('/')[1] if '/' in card_link else "Unknown"
            card_link = f'https://digitalgateopen.com/{card_link}' if not card_link.startswith('http') else card_link
        
            quantity_tag = card.select_one(".card-feature-test.align-bottom-right")
            quantity = int(quantity_tag.text.strip()) if quantity_tag and quantity_tag.text.strip().isdigit() else 0
            
            decklist.append({
                "card_ref_code": card_ref_code,
                "card_link": card_link,
                "quantity": quantity
            })
    
    return decklist

# Function to scrape detailed stats for a specific card
def scrape_card_info(card_url):
    response = requests.get(card_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    card_info = {}
    for card in soup.select('.data-container'):
        info_data_tag = card.select_one('.data-key')
        card_info_tag = card.select_one('.data-value')
        
        if info_data_tag and card_info_tag:
            card_data = info_data_tag.text.strip()
            card_value = card_info_tag.text.strip()
            card_info[card_data] = card_value
            
    return card_info

# Function to populate decklists and card data for each format
def populate_decklists_and_card_data_for_all_formats():
    for format_name, format_data in data["formats"].items():
        for tournament in format_data["tournaments"]:
            for deck in tournament["decks"]:
                deck_url = deck["deck_link"]
                if deck_url:
                    # Scrape the decklist and add it to the deck
                    deck["deck_list"] = scrape_decklist(deck_url)
                    
                    # For each card in this deck, add it to data["cards"] if it's unique
                    for card in deck["deck_list"]:
                        card_ref_code = card["card_ref_code"]
                        card_link = card["card_link"]
                        quantity = card["quantity"]
                        
                        if card_ref_code not in data["cards"]:
                            # New card: scrape card details and initialize quantities
                            card_info = scrape_card_info(card_link)
                            card_info["card_ref_code"] = card_ref_code
                            card_info["card_link"] = card_link
                            card_info["total_quantity"] = quantity
                            format_quantity_key = f"{format_name.lower().replace(' ', '_')}_quantity"
                            format_representation_key = f"{format_name.lower().replace(' ', '_')}_representation"
                            card_info[format_quantity_key] = quantity
                            card_info["total_deck_representation"] = 1
                            card_info[format_representation_key] = 1
                            
                            # Debugging: New card initialized
                            print(f"New Card: {card_ref_code} | {format_quantity_key}: {quantity} | Total Quantity: {quantity}")
                            
                            # Add the scraped card details to the main cards dictionary
                            data["cards"][card_ref_code] = card_info
                        else:
                            # Existing card: update total quantity and format-specific quantity
                            data["cards"][card_ref_code]["total_quantity"] += quantity
                            data["cards"][card_ref_code]["total_deck_representation"] += 1
                            format_quantity_key = f"{format_name.lower().replace(' ', '_')}_quantity"
                            format_representation_key = f"{format_name.lower().replace(' ', '_')}_representation"

                            if format_quantity_key in data["cards"][card_ref_code]:
                                data["cards"][card_ref_code][format_quantity_key] += quantity
                            else:
                                data["cards"][card_ref_code][format_quantity_key] = quantity
                                
                            if format_representation_key in data["cards"][card_ref_code]:
                                data["cards"][card_ref_code][format_representation_key] += 1
                            else:
                                data["cards"][card_ref_code][format_representation_key] = 1
                            
                            # Debugging: Updated card
                            print(f"Updated Card: {card_ref_code} | {format_quantity_key}: {data['cards'][card_ref_code][format_quantity_key]} | Total Quantity: {data['cards'][card_ref_code]['total_quantity']}")
                            print("total representation " + str(data["cards"][card_ref_code]["total_deck_representation"]))

def populate_decklists_and_card_data_for_local_formats():
    for format_name, format_data in data2["formats"].items():
        for tournament in format_data["tournaments"]:
            for deck in tournament["decks"]:
                deck_url = deck["deck_link"]
                if deck_url:
                    # Scrape the decklist and add it to the deck
                    deck["deck_list"] = scrape_decklist(deck_url)
                    
                    # For each card in this deck, add it to data2["cards"] if it's unique
                    for card in deck["deck_list"]:
                        card_ref_code = card["card_ref_code"]
                        card_link = card["card_link"]
                        quantity = card["quantity"]
                        
                        # Debugging: Print card details being processed
                        print(f"Processing Card: {card_ref_code} | Quantity in Deck: {quantity}")

                        if card_ref_code not in data2["cards"]:
                            # New card: scrape card details and initialize quantities
                            card_info = scrape_card_info(card_link)
                            card_info["card_ref_code"] = card_ref_code
                            card_info["card_link"] = card_link
                            card_info["total_quantity"] = quantity
                            format_quantity_key = f"{format_name.lower().replace(' ', '_')}_quantity"
                            format_representation_key = f"{format_name.lower().replace(' ', '_')}_representation"
                            card_info[format_quantity_key] = quantity
                            card_info["total_deck_representation"] = 1
                            card_info[format_representation_key] = 1
                            
                            # Debugging: New card initialized
                            print(f"New Card: {card_ref_code} | {format_quantity_key}: {quantity} | Total Quantity: {quantity}")

                            # Add the scraped card details to the main cards dictionary
                            data2["cards"][card_ref_code] = card_info
                        else:
                            # Existing card: update total quantity and format-specific quantity
                            data2["cards"][card_ref_code]["total_quantity"] += quantity
                            data2["cards"][card_ref_code]["total_deck_representation"] += 1
                            format_quantity_key = f"{format_name.lower().replace(' ', '_')}_quantity"
                            format_representation_key = f"{format_name.lower().replace(' ', '_')}_representation"

                            if format_quantity_key in data2["cards"][card_ref_code]:
                                data2["cards"][card_ref_code][format_quantity_key] += quantity
                            else:
                                data2["cards"][card_ref_code][format_quantity_key] = quantity
                                
                            if format_representation_key in data2["cards"][card_ref_code]:
                                data2["cards"][card_ref_code][format_representation_key] += 1
                            else:
                                data2["cards"][card_ref_code][format_representation_key] = 1
                            
                            # Debugging: Updated card
                            print(f"Updated Card: {card_ref_code} | {format_quantity_key}: {data2['cards'][card_ref_code][format_quantity_key]} | Total Quantity: {data2['cards'][card_ref_code]['total_quantity']}")
                            print("total representation " + str(data2["cards"][card_ref_code]["total_deck_representation"])) 


# Step 1: Get all format links for locals
#formats = get_local_format_links(local_url)

# Step 2: Load each format's locals and decks into the data structure
#for format_name, format_url in formats.items():
#   get_locals_for_format(format_url, format_name)

# Step 3: Populate decklists for all decks in each format and collect unique card information
#populate_decklists_and_card_data_for_local_formats()

# Step 1: Get all format links for tournaments
#formats = get_format_links(base_url)

# Step 2: Load each format's tournaments and decks into the data structure
#for format_name, format_url in formats.items():
#    get_tournaments_for_format(format_url, format_name)

# Step 3: Populate decklists for all decks in each format and collect unique card information
#populate_decklists_and_card_data_for_all_formats()

#%%
#import json

#save data
#with open('tournament_data.json','w') as f:
#    json.dump(data,f,indent=4)#save data
#with open('local_data.json','w') as f:
#    json.dump(data2,f,indent=4)#save data
