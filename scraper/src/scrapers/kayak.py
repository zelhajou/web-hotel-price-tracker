import json
import time
import random
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.core.driver import WebDriverManager
from src.core.logger import setup_logger
from src.utils.retry import (
    wait_for_element, 
    wait_for_elements, 
    wait_for_page_load,
    scroll_into_view
)
from src.utils.selectors import *

class KayakHotelScraper:
    def __init__(self, city, check_in_date, check_out_date):
        self.logger = setup_logger()
        self.city = city
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.base_url = "https://www.kayak.com/hotels"
        self.hotels_data = []
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        try:
            self.driver = WebDriverManager.create_driver()
            self.logger.info("WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def construct_search_url(self):
        check_in = self.check_in_date.strftime('%Y-%m-%d')
        check_out = self.check_out_date.strftime('%Y-%m-%d')
        city_formatted = self.city.replace(' ', '-')
        return f"{self.base_url}/{city_formatted}-c52508/{check_in}/{check_out}/2adults?sort=rank_a"

    def handle_popups(self):
        try:
            popup_selectors = [
                'button[aria-label="Close"]',
                '.close-button',
                '.dismiss-button'
            ]
            for selector in popup_selectors:
                try:
                    element = wait_for_element(self.driver, selector, timeout=3)
                    if element and element.is_displayed():
                        element.click()
                        time.sleep(0.5)
                except:
                    continue
        except:
            pass

    def load_page(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Loading URL (attempt {attempt + 1}): {url}")
                self.driver.get(url)
                wait_for_page_load(self.driver)
                self.handle_popups()
                
                # Scroll to load dynamic content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, 0);")
                
                return True
            except Exception as e:
                self.logger.error(f"Error loading page (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2 ** attempt)
        return False

    def extract_room_price(self, room_elem):
        """Extract price from room element with multiple selectors"""
        try:
            # Try different price selectors in order of preference
            price_selectors = [
                'span.C9NJ-amount',
                'div.C9NJ-amount', 
                'div.Ptt7-price',
                'div.c1XBO',
                'div[class*="price"]'
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = room_elem.find_element(By.CSS_SELECTOR, selector)
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Extract numeric price
                        price = float(''.join(filter(str.isdigit, price_text.replace(',', ''))))
                        return price
                except:
                    continue
            return None
        except Exception as e:
            self.logger.error(f"Error extracting room price: {str(e)}")
            return None

    def extract_room_details(self):
        """Extract detailed room information"""
        try:
            rooms = []
            # Wait and scroll for room elements
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            # Look for room containers
            room_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.LK1E-groupedRoomType')
            self.logger.info(f"Found {len(room_elements)} room elements")
            
            for room_elem in room_elements:
                try:
                    room_info = {
                        'room_type': None,
                        'price': None,
                        'bed_configuration': None,
                        'cancellation_policy': None,
                        'board_type': None,
                        'special_conditions': []
                    }
                    
                    # Scroll to room element
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", room_elem)
                    time.sleep(1)
                    
                    # Room type
                    type_elem = room_elem.find_element(By.CSS_SELECTOR, 'div.c_Hjx-group-header-title')
                    if type_elem:
                        room_info['room_type'] = type_elem.text.strip()
                    
                    # Price from provider section
                    price = self.extract_room_price(room_elem)
                    if price:
                        room_info['price'] = price
                    
                    # Bed configuration
                    bed_elems = room_elem.find_elements(By.CSS_SELECTOR, 'div.c_Hjx-detail-amenity')
                    for elem in bed_elems:
                        if any(word in elem.text.lower() for word in ['bed', 'twin', 'double', 'queen', 'king']):
                            room_info['bed_configuration'] = elem.text.strip()
                            break
                    
                    # Policies and board type
                    policy_elements = room_elem.find_elements(By.CSS_SELECTOR, '.BZag-freebie')
                    for elem in policy_elements:
                        text = elem.text.strip()
                        if 'cancellation' in text.lower():
                            room_info['cancellation_policy'] = text
                        elif 'breakfast' in text.lower():
                            room_info['board_type'] = text
                        elif text:
                            room_info['special_conditions'].append(text)
                    
                    if any(v for v in room_info.values() if v):
                        rooms.append(room_info)
                        self.logger.info(f"Successfully extracted room: {room_info['room_type']}")
                
                except Exception as e:
                    self.logger.error(f"Error extracting room details: {str(e)}")
                    continue
            
            return rooms
            
        except Exception as e:
            self.logger.error(f"Error in extract_room_details: {str(e)}")
            return []


    def extract_amenities(self):
        """Extract all amenities from the detail page"""
        amenities = []
        try:
            # Scroll to load amenities section
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get all amenity categories
            category_containers = self.driver.find_elements(By.CSS_SELECTOR, '.kml-col-12-12.kml-col-6-12-m')
            
            for container in category_containers:
                try:
                    category_name_elem = container.find_element(By.CSS_SELECTOR, '.BxLB-category-name')
                    category = category_name_elem.text.strip() if category_name_elem else None
                    
                    if category:
                        # Get all amenities in this category
                        amenity_elements = container.find_elements(By.CSS_SELECTOR, '.BxLB-amenity-name')
                        for elem in amenity_elements:
                            amenity = elem.text.strip()
                            if amenity and amenity not in amenities:
                                amenities.append(amenity)
                except:
                    continue
            
            # Also get amenities from the top summary section
            top_amenities = self.driver.find_elements(By.CSS_SELECTOR, '.t8Xi-amenity-name')
            for elem in top_amenities:
                amenity = elem.text.strip()
                if amenity and amenity not in amenities:
                    amenities.append(amenity)
                    
            return amenities
                    
        except Exception as e:
            self.logger.error(f"Error extracting amenities: {str(e)}")
            return []

    def extract_hotel_details(self, detail_url):
        """Get detailed information from hotel page"""
        try:
            self.logger.info(f"Loading detail page: {detail_url}")
            if not self.load_page(detail_url):
                return {}
            
            details = {}
            
            # Extract detail page images first
            detail_images = self.extract_detail_page_images()
            if detail_images:
                details['detail_images'] = detail_images
                self.logger.info(f"Found {len(detail_images)} detail images")
            
            # Extract rooms
            rooms = self.extract_room_details()
            if rooms:
                details['rooms'] = rooms
                self.logger.info(f"Found {len(rooms)} room types")
            
            # Extract amenities
            amenities = self.extract_amenities()
            if amenities:
                details['amenities'] = amenities
                self.logger.info(f"Found {len(amenities)} amenities")
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error extracting hotel details: {str(e)}")
            return {}


    def extract_hotel_basic_info(self, hotel_element):
        """Extract basic hotel information including images"""
        try:
            info = {}
            
            # Extract hotel name and URL
            name_elem = hotel_element.find_element(By.CSS_SELECTOR, HOTEL_NAME)
            if name_elem:
                info['hotel_name'] = name_elem.text.strip()
                info['detail_url'] = name_elem.get_attribute('href')
            
            # Extract location
            location_elem = hotel_element.find_element(By.CSS_SELECTOR, HOTEL_LOCATION)
            if location_elem:
                info['location'] = location_elem.text.strip()
            
            # Extract rating and reviews
            try:
                rating_elem = hotel_element.find_element(By.CSS_SELECTOR, HOTEL_RATING)
                reviews_elem = hotel_element.find_element(By.CSS_SELECTOR, HOTEL_REVIEWS)
                
                info['review_scores'] = {
                    'rating': float(rating_elem.text.strip()),
                    'count': int(''.join(filter(str.isdigit, reviews_elem.text)))
                }
            except:
                info['review_scores'] = {'rating': None, 'count': None}
            
            # Extract price
            try:
                price_elem = hotel_element.find_element(By.CSS_SELECTOR, PRICE_AMOUNT)
                info['price'] = price_elem.text.strip()
            except:
                info['price'] = None
            
            # Extract hotel images
            try:
                info['images'] = self.extract_hotel_images(hotel_element)
            except Exception as e:
                self.logger.error(f"Error extracting hotel images: {str(e)}")
                info['images'] = []
                
            return info
            
        except Exception as e:
            self.logger.error(f"Error extracting basic hotel info: {str(e)}")
            return None

    def extract_hotel_images(self, hotel_element):
        """Extract all available hotel images from search result"""
        images = []
        try:
            # Find the photo container directly under the hotel element
            photo_container = hotel_element.find_element(By.CSS_SELECTOR, '.e9fk-photoContainer')
            if not photo_container:
                self.logger.warning("Photo container not found")
                return []

            # Get the picture element directly
            picture_elem = photo_container.find_element(By.CSS_SELECTOR, 'picture')
            if picture_elem:
                # Get source element for mobile version
                try:
                    source_elem = picture_elem.find_element(By.CSS_SELECTOR, 'source')
                    srcset = source_elem.get_attribute('srcset')
                    if srcset:
                        mobile_url = srcset.strip()
                        images.append({
                            'url': mobile_url,
                            'alt': None,
                            'type': 'mobile'
                        })
                except:
                    self.logger.debug("No mobile source found")

                # Get the main image
                try:
                    img_elem = picture_elem.find_element(By.CSS_SELECTOR, 'img.e9fk-photo')
                    if img_elem:
                        # Get main image src
                        src = img_elem.get_attribute('src')
                        alt = img_elem.get_attribute('alt')
                        if src:
                            images.append({
                                'url': src,
                                'alt': alt,
                                'type': 'main'
                            })

                        # Get high-res versions from srcset
                        srcset = img_elem.get_attribute('srcset')
                        if srcset:
                            for src_entry in srcset.split(','):
                                src_parts = src_entry.strip().split(' ')
                                if len(src_parts) >= 1:
                                    url = src_parts[0]
                                    images.append({
                                        'url': url,
                                        'alt': alt,
                                        'type': 'high_res'
                                    })
                except:
                    self.logger.debug("No main image found")

            self.logger.info(f"Successfully extracted {len(images)} images from search page")
            return images

        except Exception as e:
            self.logger.error(f"Error in extract_hotel_images: {str(e)}")
            return []

    def extract_detail_page_images(self):
        """Extract all images from hotel detail page"""
        detail_images = []
        try:
            # Wait for the photo container to be present
            photo_container = wait_for_element(self.driver, '.c1E0k-photo-container')
            if not photo_container:
                self.logger.warning("Detail page photo container not found")
                return []

            # Get all photo items
            photo_items = self.driver.find_elements(By.CSS_SELECTOR, '.f800.f800-mod-pres-default')
            
            for item in photo_items:
                try:
                    img_elem = item.find_element(By.CSS_SELECTOR, '.f800-image')
                    src = img_elem.get_attribute('src')
                    alt = img_elem.get_attribute('alt')
                    
                    if src and src not in [img['url'] for img in detail_images]:
                        detail_images.append({
                            'url': src,
                            'alt': alt,
                            'type': 'detail'
                        })
                except:
                    continue

            self.logger.info(f"Successfully extracted {len(detail_images)} images from detail page")
            return detail_images

        except Exception as e:
            self.logger.error(f"Error extracting detail page images: {str(e)}")
            return []

    def scrape_hotels(self, limit=None):
        """Main method to scrape hotel information"""
        try:
            # Load initial search page
            search_url = self.construct_search_url()
            if not self.load_page(search_url):
                return []
            
            # Get all hotel cards first
            hotel_elements = wait_for_elements(self.driver, HOTEL_CARD)
            if not hotel_elements:
                self.logger.error("No hotel elements found")
                return []
            
            self.logger.info(f"Found {len(hotel_elements)} hotels")
            
            # Store basic info and URLs first
            hotels_to_process = []
            for hotel_element in hotel_elements[:limit]:
                try:
                    # Use our new method to extract all basic info including images
                    info = self.extract_hotel_basic_info(hotel_element)
                    if info and info.get('detail_url'):
                        hotels_to_process.append(info)
                        self.logger.info(f"Extracted basic info for: {info.get('hotel_name', 'Unknown hotel')}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting basic hotel info: {str(e)}")
                    continue
            
            # Now process each hotel's details
            for hotel_info in hotels_to_process:
                try:
                    # Get detailed info including detail page images
                    details = self.extract_hotel_details(hotel_info['detail_url'])
                    if details.get('detail_images'):
                        # Add detail images to the images array
                        hotel_info['images'].extend(details.pop('detail_images'))
                    hotel_info.update(details)
                    self.hotels_data.append(hotel_info)
                    
                    # Return to search page
                    self.load_page(search_url)
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    self.logger.error(f"Error processing hotel details: {str(e)}")
                    continue
            
            self.format_output()
            return self.hotels_data
                
        except Exception as e:
            self.logger.error(f"Error in scrape_hotels: {str(e)}")
            return []



    def format_output(self):
        """Format the scraped data into the desired structure"""
        formatted_data = {
            "city": self.city,
            "hotels": self.hotels_data,
            "pagination": {
                "current_page": 1,
                "total_pages": 1
            },
            "metadata": {
                "scraping_date": datetime.now().strftime('%Y-%m-%d'),
                "scraping_time": datetime.now().strftime('%H:%M'),
                "source_url": self.base_url
            }
        }
        self.hotels_data = formatted_data

    def save_results(self, filename='hotel_data.json'):
        try:
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.hotels_data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Data saved successfully to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {str(e)}")