# Hotel-Price-Tracker

A robust system for tracking hotel listings and prices from Kayak. The project includes a scraper for collecting hotel data and a planned Next.js frontend for displaying results.

## Overview

This project is designed to help users compare hotel prices across different dates and locations. It provides:

1. A robust scraper for collecting detailed hotel information from Kayak
2. A data storage solution for hotel listings
3. A planned Next.js frontend for displaying and filtering hotels

## Project Structure

```
hotel-price-tracker/
├── data/                   # Storage for scraped hotel data
├── docker-compose.yml      # Docker configuration
├── Dockerfile              # Container definition
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── scraper/                # Scraper module
│   ├── notebooks/          # Jupyter notebooks
│   │   └── scraper_test.ipynb  # Testing notebook
│   └── src/                # Source code
│       ├── config/         # Configuration files
│       │   └── settings.py # Scraper settings
│       ├── core/           # Core functionality
│       │   ├── driver.py   # WebDriver management
│       │   └── logger.py   # Logging setup
│       ├── scrapers/       # Scraper implementations
│       │   └── kayak.py    # Kayak hotel scraper
│       └── utils/          # Utility functions
│           ├── retry.py    # Retry mechanisms
│           └── selectors.py # CSS selectors
└── analyze_project.py      # Project analysis script
```

## Features

### Scraper Capabilities

- **Hotel Listings**: Collects detailed hotel information for specific cities
- **Room Details**: Extracts room types, prices, and availability
- **Images**: Captures hotel images from both search and detail pages
- **Amenities**: Extracts comprehensive amenity information
- **Reviews**: Collects review scores and counts
- **Robust Design**: Implements retry mechanisms and error handling
- **Rate Limiting**: Built-in delays to avoid detection

### Data Structure

The scraper stores results in a structured JSON format:

```json
{
  "city": "New York, United States",
  "hotels": [
    {
      "hotel_name": "Hotel Name",
      "detail_url": "URL to hotel detail page",
      "location": "Hotel location",
      "review_scores": {
        "rating": 8.0,
        "count": 379
      },
      "price": "$40",
      "images": [...],
      "rooms": [
        {
          "room_type": "Double Room",
          "price": 40.0,
          "bed_configuration": "1 double bed",
          "cancellation_policy": "Free cancellation",
          "board_type": "Free breakfast",
          "special_conditions": [...]
        }
      ],
      "amenities": [...]
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1
  },
  "metadata": {
    "scraping_date": "2025-01-02",
    "scraping_time": "15:01",
    "source_url": "https://www.kayak.com/hotels"
  }
}
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (if running locally)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/hotel-price-tracker.git
   cd hotel-price-tracker
   ```

2. Start the containers using Docker Compose
   ```bash
   docker-compose up -d
   ```

3. Access the Jupyter Lab interface for testing and development
   ```
   http://localhost:8888
   ```

### Running the Scraper

You can run the scraper using the provided Jupyter notebook:

1. Open `scraper_test.ipynb` in Jupyter Lab
2. Adjust the search parameters if needed:
   ```python
   city = "New York, United States"
   check_in = datetime(2025, 1, 10)
   check_out = datetime(2025, 1, 14)
   ```
3. Run all cells to execute the scraper

Alternatively, you can use the scraper in your own Python script:

```python
from datetime import datetime
from src.scrapers.kayak import KayakHotelScraper

# Initialize scraper
scraper = KayakHotelScraper(
    city="New York, United States",
    check_in_date=datetime(2025, 1, 10),
    check_out_date=datetime(2025, 1, 14)
)

# Scrape hotels (limit to 5 for testing)
results = scraper.scrape_hotels(limit=5)

# Save results
scraper.save_results()

# Close the scraper
scraper.close()
```

## Planned Frontend

The Next.js frontend is planned to include:

- Clean, responsive hotel listing layout
- Detail view for each hotel
- Room type and price comparison
- Filtering by price, star rating, amenities, etc.
- Sorting options for different criteria

## System Architecture

The system is designed for regular data collection and display:

1. **Data Collection**: Selenium-based scraper with anti-bot detection measures
2. **Data Storage**: JSON files for development, with plans for database integration
3. **Data Processing**: Python utilities for cleaning and organizing hotel data
4. **Data Presentation**: Next.js frontend with filtering capabilities

## Error Handling & Debugging

The scraper implements comprehensive error handling:

- Multiple retry attempts for transient errors
- Detailed logging for debugging
- Graceful failure handling to prevent complete scraper crashes

## Future Enhancements

- **Database Integration**: Move from JSON to a proper database
- **Regular Scheduling**: Implement automated scraping schedule
- **Expanded Sources**: Add support for additional booking sites
- **Price History**: Track and display price changes over time
- **Alerts**: Notify users of price drops or availability
- **Hotel Matching**: Cross-reference hotels across different booking sites

## Acknowledgments

- This project was created as a technical assignment
- Uses Selenium for web scraping
- Includes anti-detection measures to avoid being blocked

## Disclaimer

This tool is for educational purposes only. Web scraping may be against the Terms of Service of websites. Use responsibly and at your own risk.
