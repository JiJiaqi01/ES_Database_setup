import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone
import json

def get_publish_date(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }

    try:
        # Fetch the content from the URL
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Function to parse and convert date to GMT
            def parse_date(date_str):
                date_formats = [
                    "%Y-%m-%dT%H:%M:%SZ",      # 2020-01-01T12:00:00Z
                    "%Y-%m-%dT%H:%M:%S.%fZ",   # 2020-01-01T12:00:00.000Z
                    "%Y-%m-%dT%H:%M:%S%z",     # 2020-01-01T12:00:00+0000
                    "%Y-%m-%dT%H:%M:%S.%f%z",  # 2020-01-01T12:00:00.000+0000
                    "%Y-%m-%d",                # 2020-01-01
                    "%d %B %Y",                # 01 January 2020
                    "%B %d, %Y",               # January 01, 2020
                    "%m/%d/%Y",                # 01/01/2020
                ]
                
                for fmt in date_formats:
                    try:
                        publish_date = datetime.strptime(date_str, fmt)
                        publish_date_gmt = publish_date.astimezone(timezone.utc)
                        return publish_date_gmt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    except ValueError:
                        continue
                return None

            # Try common meta tags
            meta_tags = [
                {'name': 'date'},
                {'property': 'article:published_time'},
                {'property': 'og:published_time'},
                {'name': 'publish_date'},
                {'itemprop': 'datePublished'}
            ]
            
            for meta_tag in meta_tags:
                meta = soup.find('meta', meta_tag)
                if meta and meta.has_attr('content'):
                    date_str = meta['content']
                    parsed_date = parse_date(date_str)
                    if parsed_date:
                        return parsed_date

            # Try structured data (JSON-LD)
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    json_data = json.loads(script.string, strict=False)
                    if isinstance(json_data, list):
                        for item in json_data:
                            if 'datePublished' in item:
                                date_str = item['datePublished']
                                parsed_date = parse_date(date_str)
                                if parsed_date:
                                    return parsed_date
                    elif 'datePublished' in json_data:
                        date_str = json_data['datePublished']
                        parsed_date = parse_date(date_str)
                        if parsed_date:
                            return parsed_date
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Try visible date in content
            date_patterns = [
                r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
                r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
                r'\b\d{2} \w+ \d{4}\b',    # DD Month YYYY
                r'\b\w+ \d{2}, \d{4}\b'    # Month DD, YYYY
            ]
            
            for pattern in date_patterns:
                date_match = soup.find(string=re.compile(pattern))
                if date_match:
                    date_str = date_match.strip()
                    parsed_date = parse_date(date_str)
                    if parsed_date:
                        return parsed_date
            
            # Check for <time> tags with datetime attribute
            for time_tag in soup.find_all('time'):
                if time_tag.has_attr('datetime'):
                    date_str = time_tag['datetime']
                    parsed_date = parse_date(date_str)
                    if parsed_date:
                        return parsed_date
            
            # Check for <span> and <div> tags with date-like content
            possible_date_tags = soup.find_all(['span', 'div'], string=re.compile('|'.join(date_patterns)))
            for date_tag in possible_date_tags:
                date_str = date_tag.get_text().strip()
                parsed_date = parse_date(date_str)
                if parsed_date:
                    return parsed_date
            
            return "Publish date not found."
        else:
            return f"Failed to retrieve the web page, status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching the URL: {e}"

# Example us

# Example usage
#url = 'https://biofuels-news.com/news/celtic-renewables-in-latest-crowdfunding-boost/'
#url="https://biofuels-news.com/news/german-biodiesel-exports-surge/"
#url="https://biofuels-news.com/news/deltas-first-carbon-neutral-flight-powered-by-air-bp-supplied-biofuel/"
#url="https://ww2.arb.ca.gov/our-work/programs/low-carbon-fuel-standard"
#url="https://commission.europa.eu/strategy-and-policy/priorities-2019-2024/european-green-deal/climate-action-and-green-deal_en"
#print(get_publish_date(url))
