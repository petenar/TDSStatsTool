# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 20:13:51 2024

@author: Petr
"""
import json
# Loading data from JSON
data = {}
data2 = {}
with open('tournament_data.json', 'r') as f:
    data = json.load(f)

with open('local_data.json', 'r') as f:
    data2 = json.load(f)

# %%
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
import threading
from tkinter import messagebox
from tkinter import Toplevel
import json

base_url = "https://digitalgateopen.com/tournament-results-overview"
local_url = "https://digitalgateopen.com/local-results-overview"


try:
    with open('tournament_data.json', 'r') as f:
        data = json.load(f)
    with open('local_data.json', 'r') as f:
        data2 = json.load(f)
except FileNotFoundError:
    print("Data files not found. Please update the data.")
    data = {"formats": {}, "cards": {}}
    data2 = {"formats": {}, "cards": {}}

from Webscraping import (get_format_links,get_local_format_links,get_tournaments_for_format,get_locals_for_format,
                         scrape_decklist,scrape_card_info,populate_decklists_and_card_data_for_all_formats,
                         populate_decklists_and_card_data_for_local_formats)

# Chronological order of formats
format_order = [
    "BT4: Great Legend", "BT7: Next Adventure", "BT8: New Awakening",
    "EX2: Digital Hazard", "BT9: X Record", "BT10: Xros Encounter",
    "EX3: Draconic Roar", "BT11: Dimensional Phase", "BT12: Across Time",
    "EX4: Alternative Being", "BT13: Versus Royal Knights", "RB1: Resurgence Booster",
    "BT14: Blast Ace", "EX5: Animal Colosseum", "BT15: Exceed Apocalypse",
    "BT16: Beginning Observer", "EX6: Infernal Ascension", "BT17: Secret Crisis",
    "EX7: Digimon Liberator", "BT18-19: Special Booster Ver.2.0", "EX8: Chains of Liberation"
]


def aggregate_card_data(data, data2):
    combined_cards = {}

    for ref_code, card_info in data["cards"].items():
        combined_cards[ref_code] = {
            "Color": card_info["Color"],
            "total_quantity": card_info["total_quantity"],
            "Name": card_info["Name"],
            "total_deck_representation": card_info.get("total_deck_representation", 0),  # Start with data values
            **{k: v for k, v in card_info.items() if k.endswith("_quantity") or k.endswith("_representation")},
        }

    for ref_code, card_info in data2["cards"].items():
        if ref_code in combined_cards:
            # Add data2 values to existing data
            #combined_cards[ref_code]["total_quantity"] += card_info["total_quantity"]
            #combined_cards[ref_code]["total_deck_representation"] += card_info.get("total_deck_representation", 0)
            for key, value in card_info.items():
                if key.endswith("_quantity") or key.endswith("_representation"):
                    combined_cards[ref_code][key] = combined_cards[ref_code].get(key, 0) + value
        else:
            # Add new card from data2
            combined_cards[ref_code] = {
                "Color": card_info["Color"],
                "total_quantity": card_info["total_quantity"],
                "Name": card_info["Name"],
                "total_deck_representation": card_info.get("total_deck_representation", 0),
                **{k: v for k, v in card_info.items() if k.endswith("_quantity") or k.endswith("_representation")},
            }

    return combined_cards



# Function to get the top 25 cards by usage for any dataset
def get_top_25_cards(cards):
    """
    Get the top 25 cards by total_quantity from aggregated data.
    """
    # Sort all cards by total_quantity in descending order
    sorted_cards = sorted(cards.items(), key=lambda x: x[1]["total_quantity"], reverse=True)

    # Format the top 25 cards for display
    top_25 = [
        f"{card_ref}: {card_info['Name']} - {card_info['total_quantity']}"
        for card_ref, card_info in sorted_cards[:25]
    ]

    # Return the top 25 and the most used card's reference code
    most_used_card_ref = sorted_cards[0][0] if sorted_cards else None
    return top_25, most_used_card_ref

def display_top_25_cards():
    
    global all_card_entries  # Ensure it's a global variable
    # Clear the card display frames
    for widget in card_display_frame.winfo_children():
        widget.destroy()
    for widget in avg_rep_frame.winfo_children():
        widget.destroy()

    # Get user selections
    selected_tournament = tournament_type_var.get()
    selected_format = format_var.get()
    selected_color = color_var.get()
    selected_type = type_var.get()

    # Determine dataset
    if selected_tournament == "Regionals":
        current_data = data
    elif selected_tournament == "Unofficial Tournaments":
        current_data = data2
    else:
        current_data = {"cards": aggregate_card_data(data, data2)}
        
    #  **Debug: Print Selected Format**
    print(f"Selected Format: {selected_format}")
    
    # Apply filters for format
    filtered_cards = {}
    
    if selected_format != "All Events":
        format_quantity_key = selected_format.lower().replace(" ", "_") + "_quantity"
        format_representation_key = selected_format.lower().replace(" ", "_") + "_representation"
    
        # Get index of the selected format in format_order
        format_index = format_order.index(selected_format) if selected_format in format_order else len(format_order) - 1
        valid_formats = format_order[: format_index + 1]  # ✅ Include up to and including selected format
    
        for card_ref, card_info in current_data["cards"].items():
            total_quantity = 0
            total_representation = 0
    
            #  Sum all values up to and including the selected format
            for fmt in valid_formats:
                fmt_quantity_key = fmt.lower().replace(" ", "_") + "_quantity"
                fmt_representation_key = fmt.lower().replace(" ", "_") + "_representation"
            
                quantity = card_info.get(fmt_quantity_key, 0)
                representation = card_info.get(fmt_representation_key, 0)

                total_quantity += quantity
                total_representation += representation
    
            # Compute average copies per deck
            avg_copies_per_deck = total_quantity / total_representation if total_representation > 0 else 0
    
            #  Store in filtered_cards **if the card appears in at least one format**
            if total_quantity > 0:
                filtered_cards[card_ref] = {
                    **card_info,
                    "format_quantity": total_quantity,
                    "format_representation": total_representation,
                    "avg_copies_per_deck": avg_copies_per_deck,
                }
    

    else:
        #  No Format Selected: Use All Cards
        for card_ref, card_info in current_data["cards"].items():
            filtered_cards[card_ref] = {
                **card_info,
                "format_quantity": card_info.get("total_quantity", 0),
                "format_representation": card_info.get("total_deck_representation", 0),
                "avg_copies_per_deck": (
                    card_info.get("total_quantity", 0) / card_info.get("total_deck_representation", 1)
                ),
            }
    
    #  Debugging: Check if Cards from Selected Format Are Present
    selected_format_cards = [
        ref for ref, info in filtered_cards.items() if info["format_quantity"] > 0
    ]
    if selected_format_cards:
        print(f"🎉 Cards from {selected_format} are present in filtered_cards!")
    else:
        print(f"❌ No cards from {selected_format} found after filtering!")
    

    #  Sort cards by total quantity in the selected format
    sorted_cards_by_quantity = sorted(
        filtered_cards.items(),
        key=lambda x: x[1]["format_quantity"],
        reverse=True
    )

    
    # Display top 25 cards by quantity
    for idx, (card_ref, card_info) in enumerate(sorted_cards_by_quantity[:25], start=1):
        # Add a label above the list on the first iteration
        if idx == 1:
            heading_label = tk.Label(card_display_frame, text="Most Used Cards", font=("Arial", 14, "bold"), anchor="w")
            heading_label.pack(anchor="w", pady=(10, 5))  # Add padding for spacing
    
        # Add each card as a label
        card_label = tk.Label(card_display_frame, text=f"{card_ref}: {card_info['Name']} - {card_info['format_quantity']}",
                              font=("Arial", 10), anchor="w")
        card_label.pack(anchor="w", pady=2)


    # Calculate average representation percentage for the new list
    avg_representation_cards = []
    for card_ref, card_info in filtered_cards.items():
        total_representation = 0
        total_decks_from_release = 0
        release_format = card_ref.split("-")[0]  # Extract set prefix (e.g., "BT16")
    
        #  Sum all representation values **up to AND including the selected format**
        for format_name in format_order:
            format_representation_key = format_name.lower().replace(" ", "_") + "_representation"
    
            # 🛑 If we reached the selected format, sum it too, then stop
            total_representation += card_info.get(format_representation_key, 0)
            if format_name == selected_format:
                break
    
        #  Compute decks only up to the selected format
        if selected_tournament == "Regionals":
            total_decks_from_release = compute_total_decks(data, from_format=release_format, up_to_format=selected_format)
        elif selected_tournament == "Unofficial Tournaments":
            total_decks_from_release = compute_total_decks(data2, from_format=release_format, up_to_format=selected_format)
        else:
            total_decks_from_release = (
                compute_total_decks(data, from_format=release_format, up_to_format=selected_format) +
                compute_total_decks(data2, from_format=release_format, up_to_format=selected_format)
            )
    
        #  Debugging Output
        print(f"📌 {card_ref} | Total Representation (Up to {selected_format}): {total_representation}")
        print(f"📌 {card_ref} | Total Decks from Release (Up to {selected_format}): {total_decks_from_release}")
    
        # Compute average representation %
        avg_representation_percentage = (
            total_representation / total_decks_from_release * 100 if total_decks_from_release > 0 else 0
        )
    
        avg_representation_cards.append((card_ref, card_info["Name"], avg_representation_percentage))
    
        if card_ref == "BT16-082":
            print("✅ Debugging BT16-082:")
            print("Decks:", total_decks_from_release)
            print("Decks Played in:", total_representation)
            print("Average Representation %:", avg_representation_percentage)
    
    #  Sort by average representation percentage
    avg_representation_cards = sorted(avg_representation_cards, key=lambda x: x[2], reverse=True)

    
    # Add a title label above the list
    avg_heading_label = tk.Label(avg_rep_frame, text="Highest Average Representation", font=("Arial", 14, "bold"), anchor="w")
    avg_heading_label.pack(anchor="w", pady=(10, 5))  # Adjust the padding as necessary
    
    # Display top 25 cards by average representation percentage
    for idx, (card_ref, card_name, avg_representation) in enumerate(avg_representation_cards[:25], start=1):
        avg_rep_label = tk.Label(avg_rep_frame, text=f"{card_ref}: {card_name} - {avg_representation:.2f}%",
                                 font=("Arial", 10), anchor="w")
        avg_rep_label.pack(anchor="w", pady=2)
        
     # Update the global `all_card_entries`
    all_card_entries = [f"{ref}: {info['Name']}" for ref, info in filtered_cards.items()]

    # Populate card dropdown
    card_dropdown["values"] = sorted(all_card_entries)

    if not filtered_cards:
        print("No cards found after filtering!")
        return




# Function to update the format dropdown with all formats
def populate_format_dropdown():
    # Populate with all unique formats from both datasets
    all_formats = set(data["formats"].keys()).union(set(data2["formats"].keys()))
    formats = ["All Events"] + sorted(all_formats)  # Add "All Events" as the first option
    format_dropdown["values"] = formats
    format_dropdown.set("All Events")  # Default to "All Events"

def populate_card_dropdown(filtered_cards):
    global all_card_entries  # Keep a global reference to the full list of cards
    all_card_entries = [f"{ref_code}: {card_info['Name']}" for ref_code, card_info in filtered_cards.items()]
    card_dropdown["values"] = sorted(all_card_entries)  # Populate the dropdown with sorted entries
    card_var.set("")  # Clear previous selection
    
def filter_card_dropdown(event):
    # Get the current input in the dropdown
    typed_text = card_var.get()

    # Filter the full list of card options based on the input
    filtered_entries = [entry for entry in all_card_entries if typed_text.lower() in entry.lower()]

    # Update the dropdown values with the filtered list
    card_dropdown["values"] = filtered_entries

def generate_image_url(card_ref_code):
    base_url = "https://digitalgateopen.com/images/cards/"
    format_code = card_ref_code.split('-')[0]  # Extract the format code
    return f"{base_url}{format_code}/{card_ref_code}.webp"

def compute_total_decks(dataset, from_format=None, up_to_format=None):
    total_decks = 0
    formats = dataset.get("formats", {})
    format_started = False
    format_stopped = False


    for format_name in format_order:
        # Skip formats until we reach the starting format
        if from_format and not format_started:
            if format_name.startswith(from_format):
                format_started = True
            else:
                continue

        # Stop counting when we reach `up_to_format`
        if up_to_format and format_name == up_to_format:
            format_stopped = True



        # Process decks in the current format
        format_data = formats.get(format_name, {})
        tournaments = format_data.get("tournaments", {})

        if isinstance(tournaments, list):  # Handle list-based structure
            for tournament in tournaments:
                total_decks += len(tournament.get("decks", []))
        elif isinstance(tournaments, dict):  # Handle dict-based structure
            for tournament in tournaments.values():
                total_decks += len(tournament.get("decks", []))

        # Stop if we reached up_to_format
        if format_stopped:
            break


    return total_decks




def display_card_statistics(card_ref_code):
    """
    Computes and displays statistics for the selected card:
    - Competitive Copies Run
    - Casual Copies Run
    - Overall Competitive Representation
    - Overall Casual Representation
    - Overall Representation
    - Average Copies Run
    - Average Representation Percentage
    """
    # Ensure the frame exists
    global stats_display_frame
    if not stats_display_frame.winfo_exists():
        stats_display_frame = tk.Frame(card_content_frame)
        stats_display_frame.pack(pady=10)



    # Identify the release format based on the card reference code
    release_format = card_ref_code.split("-")[0]  # Extract prefix (e.g., `BT16`)
    
    # Prepare stats
    stats = {
        "competitive": {
            "total_quantity": 0,
            "total_representation": 0,
            "total_decks": compute_total_decks(data),
            "total_decks_from_release": compute_total_decks(data, from_format=release_format),
        },
        "casual": {
            "total_quantity": 0,
            "total_representation": 0,
            "total_decks": compute_total_decks(data2),
            "total_decks_from_release": compute_total_decks(data2, from_format=release_format),
        },
        "aggregate": {
            "total_quantity": 0,
            "total_representation": 0,
            "total_decks": compute_total_decks({"formats": {**data["formats"], **data2["formats"]}}),
            "total_decks_from_release": compute_total_decks(data, from_format=release_format) + compute_total_decks(data2, from_format=release_format)
        },
    }

    card_data = {
        "competitive": data["cards"].get(card_ref_code, {}),
        "casual": data2["cards"].get(card_ref_code, {}),
        "aggregate": aggregate_card_data(data, data2).get(card_ref_code, {}),
    }

    for key, dataset in stats.items():
        card_info = card_data[key]
        dataset["total_quantity"] = card_info.get("total_quantity", 0)
        if key == "aggregate":
            dataset["total_representation"] = (
                card_data["competitive"].get("total_deck_representation", 0) +
                card_data["casual"].get("total_deck_representation", 0)
            )
        else:
            dataset["total_representation"] = card_info.get("total_deck_representation", 0)

    # Calculate average comp copies run
    avg_comp_copies_run = (
        stats["competitive"]["total_quantity"] / stats["competitive"]["total_representation"]
        if stats["competitive"]["total_representation"] > 0
        else 0
    )
    # Calculate average casual copies run
    avg_casual_copies_run = (
        stats["casual"]["total_quantity"] / stats["casual"]["total_representation"]
        if stats["casual"]["total_representation"] > 0
        else 0
    )
    # Calculate average copies run
    avg_copies_run = (
        stats["aggregate"]["total_quantity"] / stats["aggregate"]["total_representation"]
        if stats["aggregate"]["total_representation"] > 0
        else 0
    )

    # Calculate average comp representation percentage
    avg_comp_representation_percentage = (
        stats["competitive"]["total_representation"] / stats["competitive"]["total_decks_from_release"] * 100
        if stats["competitive"]["total_decks_from_release"] > 0
        else 0
    )
    # Calculate average casual representation percentage
    avg_casual_representation_percentage = (
        stats["casual"]["total_representation"] / stats["casual"]["total_decks_from_release"] * 100
        if stats["casual"]["total_decks_from_release"] > 0
        else 0
    )
    # Calculate average representation percentage
    avg_representation_percentage = (
        stats["aggregate"]["total_representation"] / stats["aggregate"]["total_decks_from_release"] * 100
        if stats["aggregate"]["total_decks_from_release"] > 0
        else 0
    )

    stats_text = f"""
    Decks played in since release (Aggregate): {stats['aggregate']['total_representation']}
    Decks played since release (Aggregate): {stats['aggregate']['total_decks_from_release']}
    Decks played in since release (Regionals): {stats['competitive']['total_representation']}
    Decks played since release (Regionals): {stats['competitive']['total_decks_from_release']}
    Decks played in since release (Casual): {stats['casual']['total_representation']}
    Decks played since release (Casual): {stats['casual']['total_decks_from_release']}
    Competitive Copies Run: {stats['competitive']['total_quantity']}
    Casual Copies Run: {stats['casual']['total_quantity']}
    Average Copies Run (Regionals): {avg_comp_copies_run:.2f}
    Average Copies Run (Casual): {avg_casual_copies_run:.2f}
    Average Copies Run (Aggregate): {avg_copies_run:.2f}
    Average Representation Percentage (Regionals): {avg_comp_representation_percentage:.2f}%
    Average Representation Percentage (Casual): {avg_casual_representation_percentage:.2f}%
    Average Representation Percentage (Aggregate): {avg_representation_percentage:.2f}%
    Overall Competitive Representation: {
        (stats['competitive']['total_representation'] / stats['competitive']['total_decks'] * 100 if stats['competitive']['total_decks'] > 0 else 0):.2f}%
    Overall Casual Representation: {
        (stats['casual']['total_representation'] / stats['casual']['total_decks'] * 100 if stats['casual']['total_decks'] > 0 else 0):.2f}%
    Overall Representation: {
        (stats['aggregate']['total_representation'] / stats['aggregate']['total_decks'] * 100 if stats['aggregate']['total_decks'] > 0 else 0):.2f}%

    """

    # Debugging: Print stats
    print(stats_text)

    # Clear the frame and display the stats
    for widget in stats_display_frame.winfo_children():
        widget.destroy()

    stats_label = tk.Label(stats_display_frame, text=stats_text, font=("Arial", 10), justify="left", anchor="w")
    stats_label.pack(fill="x")


def display_card_image(card_ref_code):
    # Generate the image URL
    image_url = generate_image_url(card_ref_code)
    print(f"Generated Image URL: {image_url}")  # Debugging

    try:
        # Determine dataset based on selected tournament type and format
        selected_tournament = tournament_type_var.get()
        selected_format = format_var.get()

        # Use the aggregate dataset for initial population or "All Events"
        if selected_tournament == "All Events":
            current_data = {"cards": aggregate_card_data(data, data2)}
        elif selected_tournament == "Regionals":
            current_data = data
        elif selected_tournament == "Unofficial Tournaments":
            current_data = data2
        else:
            current_data = {"cards": aggregate_card_data(data, data2)}

        # Fetch the card information from the current dataset
        card_info = current_data["cards"].get(card_ref_code, None)

        # Update card information display
        if card_info:
            card_name = card_info["Name"]

            # Fetch the relevant quantity based on the selected format
            if selected_format != "All Events":
                format_quantity_key = selected_format.lower().replace(" ", "_") + "_quantity"
                quantity = card_info.get(format_quantity_key, 0)
            else:
                quantity = card_info.get("total_quantity", 0)

            # Update the card info label
            card_info_label.config(
                text=f"{card_ref_code}: {card_name}\nQuantity: {quantity}"
            )
        else:
            card_info_label.config(text=f"{card_ref_code}: Card Info Not Found")

        # Fetch and display the card image
        response = requests.get(image_url)
        response.raise_for_status()

        # Open and resize the image
        img_data = Image.open(BytesIO(response.content))
        img_data = img_data.resize((250, 350), Image.ANTIALIAS)

        # Convert to ImageTk for Tkinter
        img = ImageTk.PhotoImage(img_data)

        # Clear existing image widgets in the subframe
        for widget in card_content_frame.winfo_children():
            if widget != card_info_label:  # Keep the label
                widget.destroy()

        # Display the image
        img_label = tk.Label(card_content_frame, image=img)
        img_label.image = img  # Keep a reference to avoid garbage collection
        img_label.pack(pady=5)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching card image: {e}")
    except Exception as e:
        print(f"Error displaying card image: {e}")
        
    display_card_graphs(card_ref_code)
    display_card_statistics(card_ref_code)

def plot_card_usage_over_time(card_ref_code, dataset, graph_title, parent_frame):
    """
    Plots card usage over time from the specified dataset.

    :param card_ref_code: Reference code of the card to plot.
    :param dataset: The dataset to use ('aggregate' or 'regionals').
    :param graph_title: Title for the graph.
    :param parent_frame: Frame in which to embed the graph.
    """
    # Choose dataset
    if dataset == "aggregate":
        aggregated_data = aggregate_card_data(data, data2)
    elif dataset == "regionals":
        aggregated_data = data["cards"]
    else:
        print(f"Invalid dataset: {dataset}")
        return

    # Ensure the card exists in the dataset
    if card_ref_code not in aggregated_data:
        print(f"No data found for card {card_ref_code} in dataset {dataset}")
        return

    # Fetch card information
    card_info = aggregated_data[card_ref_code]

    # Prepare data for the graph
    usage_by_format = {}
    for format_name in format_order:
        format_key = format_name.lower().replace(" ", "_") + "_quantity"
        usage_by_format[format_name] = card_info.get(format_key, 0)

    # Remove formats with 0 quantity before the first non-zero occurrence
    formats = []
    quantities = []
    non_zero_found = False
    for fmt, qty in usage_by_format.items():
        if qty > 0 or non_zero_found:
            non_zero_found = True
            formats.append(fmt)
            quantities.append(qty)

    # Create the graph
    fig, ax = plt.subplots(figsize=(4, 3))  # Adjust size as needed
    ax.plot(formats, quantities, marker="o", linestyle="-", color="blue")
    ax.set_title(graph_title, fontsize=12)
    ax.set_xlabel("Formats", fontsize=10)
    ax.set_ylabel("Quantity", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(visible=True, linestyle="--", alpha=0.5)
    ax.set_xticklabels([abbr.split(":")[0] for abbr in formats], rotation=45, fontsize=8)
    plt.tight_layout()

    # Clear the parent frame
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Embed the graph into the Tkinter application
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    canvas.draw()

def plot_representation_by_format(card_ref_code, dataset, graph_title, parent_frame):
    """
    Plots deck representation by format from the specified dataset.

    :param card_ref_code: Reference code of the card to plot.
    :param dataset: The dataset to use ('aggregate' or 'regionals').
    :param graph_title: Title for the graph.
    :param parent_frame: Frame in which to embed the graph.
    """
    # Choose dataset
    if dataset == "aggregate":
        aggregated_data = aggregate_card_data(data, data2)
    elif dataset == "regionals":
        aggregated_data = data["cards"]
    else:
     #   print(f"Invalid dataset: {dataset}")
        return

    # Ensure the card exists in the dataset
    if card_ref_code not in aggregated_data:
      #  print(f"No data found for card {card_ref_code} in dataset {dataset}")
        return

    # Fetch card information
    card_info = aggregated_data[card_ref_code]

    # Prepare data for the graph
    representation_by_format = {}
    for format_name in format_order:
        # Generate the format-specific representation key
        format_key = format_name.lower().replace(" ", "_") + "_representation"
        representation_by_format[format_name] = card_info.get(format_key, 0)

    # Remove formats with 0 representation before the first non-zero occurrence
    formats = []
    representations = []
    non_zero_found = False
    for fmt, rep in representation_by_format.items():
        if rep > 0 or non_zero_found:
            non_zero_found = True
            formats.append(fmt)
            representations.append(rep)

    # Create the graph
    fig, ax = plt.subplots(figsize=(4, 3))  # Adjust size as needed
    ax.bar(formats, representations, color="green")
    ax.set_title(graph_title, fontsize=12)
    ax.set_xlabel("Formats", fontsize=10)
    ax.set_ylabel("Deck Representation", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(visible=True, linestyle="--", alpha=0.5)
    ax.set_xticklabels([abbr.split(":")[0] for abbr in formats], rotation=45, fontsize=8)
    plt.tight_layout()

    # Clear the parent frame
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Embed the graph into the Tkinter application
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    canvas.draw()


def display_card_graphs(card_ref_code):
    """
    Displays all graphs for the selected card: 2x2 grid of usage and representation
    plus 2x1 grid of representation as percentage.
    """
    # Aggregate Usage
    plot_card_usage_over_time(
        card_ref_code,
        dataset="aggregate",
        graph_title="Overall Usage Over Time",
        parent_frame=aggregate_graph_frame
    )

    # Competitive Usage (Regionals)
    plot_card_usage_over_time(
        card_ref_code,
        dataset="regionals",
        graph_title="Competitive Usage Over Time",
        parent_frame=regionals_graph_frame
    )

    # Deck Representation by Format (Aggregate)
    plot_representation_by_format(
        card_ref_code,
        dataset="aggregate",
        graph_title="Deck Representation by Format",
        parent_frame=representation_graph_frame
    )

    # Competitive Deck Representation by Format (Regionals)
    plot_representation_by_format(
        card_ref_code,
        dataset="regionals",
        graph_title="Competitive Deck Representation by Format",
        parent_frame=competitive_representation_graph_frame
    )

    # Representation as Percentage (Regionals)
    plot_representation_percentage(
        card_ref_code,
        dataset="regionals",
        graph_title="Competitive Representation as a %",
        parent_frame=competitive_percentage_graph_frame
    )

    # Representation as Percentage (Unofficial)
    plot_representation_percentage(
        card_ref_code,
        dataset="unofficial",
        graph_title="Unofficial Representation as a %",
        parent_frame=unofficial_percentage_graph_frame
    )

# Modify `on_card_selected` to include graph plotting
def on_card_selected():
    # Get the selected card from the dropdown
    selected_card = card_var.get()

    if selected_card:
        # Extract the card reference code (everything before the colon `:`)
        selected_ref_code = selected_card.split(":")[0].strip()
        print(f"Selected Card Ref Code: {selected_ref_code}")  # Debugging

        # Use the aggregate dataset for fetching card info
        aggregated_data = aggregate_card_data(data, data2)

        if selected_ref_code in aggregated_data:
            # Fetch card info from the aggregated data
            card_info = aggregated_data[selected_ref_code]

            # Display the card image and info
            display_card_image(selected_ref_code)

            # Update the card info label with aggregated total quantity
            card_name = card_info["Name"]
            total_quantity = card_info.get("total_quantity", 0)
            card_info_label.config(
                text=f"{selected_ref_code}: {card_name}\nTotal Quantity: {total_quantity}"
            )

            # Plot the graph for the selected card
            display_card_graphs(selected_ref_code)

            # Plot average copies per deck
            plot_average_copies_per_deck(
                selected_ref_code,
                dataset="regionals",  # Only for competitive usage
                graph_title="Average Copies per Deck (Competitive)",
                parent_frame=avg_copies_graph_frame
            )           
  
def plot_representation_percentage(card_ref_code, dataset, graph_title, parent_frame):
    if dataset == "regionals":
        selected_data = data
    elif dataset == "unofficial":
        selected_data = data2
    else:
     #   print(f"Invalid dataset: {dataset}")
        return

    # Ensure the card exists in the dataset
    if card_ref_code not in selected_data["cards"]:
     #   print(f"No data found for card {card_ref_code} in dataset {dataset}")
        return

    # Fetch card information
    card_info = selected_data["cards"][card_ref_code]

    # Prepare data for the graph
    percentage_by_format = {}
    total_decks_all_formats = 0
    for format_name in format_order:
        representation_key = format_name.lower().replace(" ", "_") + "_representation"
        representation = card_info.get(representation_key, 0)

        total_decks = 0
        format_key = format_name
        if format_key in selected_data["formats"]:
            tournaments = selected_data["formats"][format_key].get("tournaments", [])
            if isinstance(tournaments, list):
                total_decks = sum(len(tournament.get("decks", [])) for tournament in tournaments)
            elif isinstance(tournaments, dict):
                total_decks = sum(len(tournament.get("decks", [])) for tournament in tournaments.values())
                
        total_decks_all_formats += total_decks
        #print(f"Format: {format_name}, Representation: {representation}, Total Decks: {total_decks}")

        if total_decks > 0:
            percentage_by_format[format_name] = (representation / total_decks) * 100
        else:
            percentage_by_format[format_name] = 0

    # Filter formats with valid data
    formats = []
    percentages = []
    non_zero_found = False
    for fmt, perc in percentage_by_format.items():
        if perc > 0 or non_zero_found:
            non_zero_found = True
            formats.append(fmt)
            percentages.append(perc)

   # print(f"Filtered Formats: {formats}")
   # print(f"Filtered Percentages: {percentages}")

    if not formats or not percentages:
    #    print(f"No data to plot for card {card_ref_code} in dataset {dataset}")
        return

    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(formats, percentages, color="purple")
    ax.set_title(graph_title, fontsize=12)
    ax.set_xlabel("Formats", fontsize=10)
    ax.set_ylabel("Representation (%)", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(visible=True, linestyle="--", alpha=0.5)
    ax.set_xticklabels([abbr.split(":")[0] for abbr in formats], rotation=45, fontsize=8)
    plt.tight_layout()

    for widget in parent_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    canvas.draw()
  
def plot_average_copies_per_deck(card_ref_code, dataset, graph_title, parent_frame):
    """
    Plots the average copies per deck for a card in competitive events.

    :param card_ref_code: Reference code of the card to plot.
    :param dataset: The dataset to use ('regionals').
    :param graph_title: Title for the graph.
    :param parent_frame: Frame in which to embed the graph.
    """
    # Use the specified dataset
    if dataset == "regionals":
        selected_data = data
    else:
        print(f"Invalid dataset: {dataset}")
        return

    # Ensure the card exists in the dataset
    if card_ref_code not in selected_data["cards"]:
        print(f"No data found for card {card_ref_code} in dataset {dataset}")
        return

    # Fetch card information
    card_info = selected_data["cards"][card_ref_code]

    # Prepare data for the graph
    usage_by_format = {}
    representation_by_format = {}

    for format_name in format_order:
        # Get the quantity of the card in the format
        quantity_key = format_name.lower().replace(" ", "_") + "_quantity"
        usage_by_format[format_name] = card_info.get(quantity_key, 0)

        # Get the representation (number of decks with the card) in the format
        representation_key = format_name.lower().replace(" ", "_") + "_representation"
        representation_by_format[format_name] = card_info.get(representation_key, 0)

    # Calculate average copies per deck with the card
    average_copies_per_deck = [
        (usage_by_format[fmt] / representation_by_format[fmt] if representation_by_format[fmt] > 0 else 0)
        for fmt in format_order
    ]

    # Debugging outputs
    print("Debugging: Usage by Format:", usage_by_format)
    print("Debugging: Representation by Format:", representation_by_format)
    print("Debugging: Average Copies per Deck:", average_copies_per_deck)

    # Remove formats with 0 average copies before the first non-zero occurrence
    formats = []
    averages = []
    non_zero_found = False
    for fmt, avg in zip(format_order, average_copies_per_deck):
        if avg > 0 or non_zero_found:
            non_zero_found = True
            formats.append(fmt)
            averages.append(avg)

    # Plot if data exists
    if not formats or not averages:
        print(f"No data to plot for card {card_ref_code} in dataset {dataset}")
        return

    # Create the graph
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(formats, averages, color="blue")
    ax.set_title(graph_title, fontsize=12)
    ax.set_xlabel("Formats", fontsize=10)
    ax.set_ylabel("Average Copies per Deck", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(visible=True, linestyle="--", alpha=0.5)
    ax.set_xticklabels([abbr.split(":")[0] for abbr in formats], rotation=45, fontsize=8)
    plt.tight_layout()

    # Clear the parent frame
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Embed the graph into the Tkinter application
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    canvas.draw()

# Initialize the UI
root = tk.Tk()
root.title("TDS Stats Tool")
root.geometry("1800x1000")  # Wider window

def open_donation_link():
    """Opens the PayPal donation link in the user's default web browser."""
    donation_url = "https://www.paypal.com/donate/?business=SFNMDRWRLCGKG&no_recurring=0&currency_code=USD"  # Replace with your PayPal link
    webbrowser.open(donation_url)

# Add a "Donate" button to the UI
donate_button = tk.Button(
    root, 
    text="Donate", 
    font=("Arial", 12, "bold"), 
    fg="white", 
    bg="green", 
    command=open_donation_link
)

def update_data():
    """
    Updates the local and tournament data by running the scraper.
    Writes the data to JSON files upon completion.
    Ensures the update thread terminates when the application is closed.
    """
    # Create the popup
    loading_popup = Toplevel(root)
    loading_popup.title("Updating Data")
    loading_popup.geometry("300x100")

    loading_label = tk.Label(loading_popup, text="Update in progress. Please wait...")
    loading_label.pack(pady=10)

    loading_bar = ttk.Progressbar(loading_popup, mode="indeterminate")
    loading_bar.pack(fill="x", padx=20, pady=10)
    loading_bar.start(10)

    # Flag to indicate if the update thread should stop
    stop_event = threading.Event()

    def run_update():
        try:
            # Step 1: Get all format links for locals
            formats = get_local_format_links(local_url)

             #Step 2: Load each format's locals and decks into the data structure
            for format_name, format_url in formats.items():
                get_locals_for_format(format_url, format_name)

             #Step 3: Populate decklists for all decks in each format and collect unique card information
            populate_decklists_and_card_data_for_local_formats()

             #Step 1: Get all format links for tournaments
            formats = get_format_links(base_url)

             #Step 2: Load each format's tournaments and decks into the data structure
            for format_name, format_url in formats.items():
                get_tournaments_for_format(format_url, format_name)

             #Step 3: Populate decklists for all decks in each format and collect unique card information
            populate_decklists_and_card_data_for_all_formats()

            # Save the updated data
            with open('tournament_data.json', 'w') as f:
                json.dump(data, f, indent=4)
            with open('local_data.json', 'w') as f:
                json.dump(data2, f, indent=4)

            messagebox.showinfo("Update Complete", "Data has been successfully updated.")
        except Exception as e:
            messagebox.showerror("Update Failed", f"An error occurred during the update: {e}")
        finally:
            loading_bar.stop()
            loading_popup.destroy()

    # Terminate the update process if the popup is closed
    def stop_update():
        stop_event.set()  # Signal the thread to stop
        loading_popup.destroy()

    # Bind closing of the popup window to stopping the update process
    loading_popup.protocol("WM_DELETE_WINDOW", stop_update)

    # Start the update in a separate thread
    update_thread = threading.Thread(target=run_update)
    update_thread.start()

donate_button.pack(pady=10, side="top")

#Add an "Update" button to the UI
update_button = tk.Button(
    root, 
    text="Update Data", 
    font=("Arial", 12, "bold"), 
    fg="white", 
    bg="Blue", 
    command=update_data
)

update_button.pack(pady=10)
# Dropdowns
dropdown_frame = tk.Frame(root)
dropdown_frame.pack(pady=10)

# Tournament type dropdown
tournament_type_var = tk.StringVar(value="All Events")
tournament_type_dropdown = ttk.Combobox(dropdown_frame, textvariable=tournament_type_var, state="readonly")
tournament_type_dropdown["values"] = ["All Events", "Unofficial Tournaments", "Regionals"]
tournament_type_dropdown.pack(side="left", padx=10)

# Format dropdown
format_var = tk.StringVar(value="All Events")
format_dropdown = ttk.Combobox(dropdown_frame, textvariable=format_var, state="readonly")
format_dropdown.pack(side="left", padx=10)

# Color dropdown
color_var = tk.StringVar(value="All")
color_dropdown = ttk.Combobox(dropdown_frame, textvariable=color_var, state="readonly")
color_dropdown["values"] = ["All", "Red", "Yellow", "Green", "Blue", "Purple", "Black", "White"]
color_dropdown.pack(side="left", padx=10)

# Add a dropdown for card type filtering
type_var = tk.StringVar(value="All")
type_dropdown = ttk.Combobox(dropdown_frame, textvariable=type_var, state="readonly")
type_dropdown["values"] = ["All", "Digitama", "Option", "Tamer", "Rookie", "Champion", "Ultimate", "Mega"]
type_dropdown.pack(side="left", padx=10)

# Card selection dropdown
card_var = tk.StringVar()
card_dropdown = ttk.Combobox(dropdown_frame, textvariable=card_var, state="normal")
card_dropdown.pack(side="left", padx=10)


# Main frame to hold the left and right sections
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

# Frame for displaying top 25 cards by average representation percentage (leftmost)
avg_rep_frame = tk.Frame(main_frame)
avg_rep_frame.pack(side="left", padx=10, pady=20, fill="y", expand=True)

# Frame for displaying text (left side)
card_display_frame = tk.Frame(main_frame)
card_display_frame.pack(side="left", padx=10, pady=20, fill="y", expand=True)


# Frame for displaying the image (right side)
card_image_frame = tk.Frame(main_frame)
card_image_frame.pack(side="right", padx=10, pady=20, fill="both", expand=True)

# Frame to hold both rows of graphs
graph_frame = tk.Frame(main_frame)
graph_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Subframes for individual graphs
aggregate_graph_frame = tk.Frame(graph_frame)
aggregate_graph_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

regionals_graph_frame = tk.Frame(graph_frame)
regionals_graph_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

representation_graph_frame = tk.Frame(graph_frame)
representation_graph_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

competitive_representation_graph_frame = tk.Frame(graph_frame)
competitive_representation_graph_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

# Subframes for representation as percentage graphs
competitive_percentage_graph_frame = tk.Frame(graph_frame)
competitive_percentage_graph_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

unofficial_percentage_graph_frame = tk.Frame(graph_frame)
unofficial_percentage_graph_frame.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

avg_copies_graph_frame = tk.Frame(graph_frame)
avg_copies_graph_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

# Configure row and column weights for graph_frame
graph_frame.rowconfigure(0, weight=1)
graph_frame.rowconfigure(1, weight=1)
graph_frame.rowconfigure(2, weight=1)  # Add weight for the third row
graph_frame.columnconfigure(0, weight=1)
graph_frame.columnconfigure(1, weight=1)

# Subframe to hold the label and image
card_content_frame = tk.Frame(card_image_frame)
card_content_frame.pack(pady=10)

# Card info label (above the image)
card_info_label = tk.Label(card_content_frame, text="", font=("Arial", 12, "italic"), wraplength=300, justify="center")
card_info_label.pack(pady=(5, 10))

# Frame for displaying statistics beneath the card image
stats_display_frame = tk.Frame(card_content_frame)
stats_display_frame.pack(pady=10)


# Bindings
color_dropdown.bind("<<ComboboxSelected>>", lambda event: display_top_25_cards())
tournament_type_dropdown.bind("<<ComboboxSelected>>", lambda event: display_top_25_cards())
format_dropdown.bind("<<ComboboxSelected>>", lambda event: display_top_25_cards())
card_dropdown.bind("<KeyRelease>", filter_card_dropdown)
card_dropdown.bind("<<ComboboxSelected>>", lambda event: on_card_selected())
type_dropdown.bind("<<ComboboxSelected>>", lambda event: display_top_25_cards())

# Populate format dropdown and initialize display
populate_format_dropdown()

# Initialize the display with the top 25 most used cards (All)
top_25_cards, most_used_card_ref = get_top_25_cards(aggregate_card_data(data, data2))
display_top_25_cards()

# Display the image and stats for the most used card
if most_used_card_ref:
    display_card_image(most_used_card_ref)
    display_card_graphs(most_used_card_ref)
    plot_card_usage_over_time(
        most_used_card_ref,
        dataset="aggregate",
        graph_title="Overall Usage Over Time",
        parent_frame=aggregate_graph_frame
    )
    plot_average_copies_per_deck(
        most_used_card_ref,
        dataset="regionals",  # Only for competitive usage
        graph_title="Average Copies per Deck (Competitive)",
        parent_frame=avg_copies_graph_frame
    )
    
def compute_card_statistics(card_ref_code, dataset):
    """Compute and print statistics for a given card."""
    
    # Select the dataset
    if dataset == "regionals":
        selected_data = data
    elif dataset == "unofficial":
        selected_data = data2
    else:
        print(f"Invalid dataset: {dataset}")
        return

    # Ensure the card exists in the dataset
    if card_ref_code not in selected_data["cards"]:
        print(f"No data found for card {card_ref_code} in dataset {dataset}")
        return

    # Fetch card information
    card_info = selected_data["cards"][card_ref_code]

    # Initialize variables for total counts
    total_decks = 0
    total_decks_all_formats = 0
    total_representation = 0
    total_quantity = 0

    # Iterate over format_order to calculate total decks, representation, and quantity
    for format_name in format_order:
        representation_key = format_name.lower().replace(" ", "_") + "_representation"
        representation = card_info.get(representation_key, 0)
        total_representation += representation
        
        total_decks = 0
        format_key = format_name
        if format_key in selected_data["formats"]:
            tournaments = selected_data["formats"][format_key].get("tournaments", [])
            if isinstance(tournaments, list):
                total_decks = sum(len(tournament.get("decks", [])) for tournament in tournaments)
            elif isinstance(tournaments, dict):
                total_decks = sum(len(tournament.get("decks", [])) for tournament in tournaments.values())

        # Accumulate total decks across all formats
        total_decks_all_formats += total_decks

    # Fetch total quantities for the card from both datasets
    competitive_copies = data["cards"].get(card_ref_code, {}).get("total_quantity", 0)
    casual_copies = data2["cards"].get(card_ref_code, {}).get("total_quantity", 0)
    total_quantity = competitive_copies + casual_copies

    # Calculate percentages
    representation_percentage = (total_representation / total_decks_all_formats * 100) if total_decks else 0

    # Print the stats to the terminal
    print(f"Competitive Copies Run: {competitive_copies}")
    print(f"Casual Copies Run: {casual_copies}")
    print(f"Representation in This Format: {representation_percentage:.2f}%")
    print(f"Total Decks: {total_decks_all_formats}")
    print(f"Total Quantity: {total_quantity}")


# Example usage
#compute_card_statistics("BT16-082", "unofficial")
total_comp = compute_total_decks(data,from_format='BT16')
print(str(total_comp))
total_casual = compute_total_decks(data2,from_format='BT16')
print(str(total_casual))
aggregate = compute_total_decks(data,from_format='BT16') + compute_total_decks(data2,from_format='BT16')
print(str(aggregate))
# Run the UI
root.mainloop()

