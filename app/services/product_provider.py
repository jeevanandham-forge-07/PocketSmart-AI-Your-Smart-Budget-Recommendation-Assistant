import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, List


class BaseProductProvider(ABC):
    """Abstract base provider for search links and product mappings"""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    def generate_search_url(self, search_term: str, city: str = "") -> str:
        pass


class AmazonProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "Amazon"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        encoded = urllib.parse.quote_plus(search_term.strip())
        return f"https://www.amazon.in/s?k={encoded}"


class FlipkartProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "Flipkart"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        encoded = urllib.parse.quote_plus(search_term.strip())
        return f"https://www.flipkart.com/search?q={encoded}"


class IkeaProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "IKEA"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        encoded = urllib.parse.quote_plus(search_term.strip())
        return f"https://www.ikea.com/in/en/search/?q={encoded}"


class SwiggyProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "Swiggy"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        encoded = urllib.parse.quote_plus(f"{search_term} {city}".strip())
        return f"https://www.swiggy.com/search?query={encoded}"


class ZomatoProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "Zomato"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        city_slug = city.lower().replace(" ", "-") if city else "india"
        encoded = urllib.parse.quote_plus(search_term.strip())
        return f"https://www.zomato.com/{city_slug}/restaurants?q={encoded}"


class OyoProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "OYO"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        target = f"{city} {search_term}".strip() if city else search_term.strip()
        encoded = urllib.parse.quote_plus(target)
        return f"https://www.oyorooms.com/search?location={encoded}"


class MakeMyTripProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "MakeMyTrip"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        encoded = urllib.parse.quote_plus(f"{city} {search_term}".strip())
        return f"https://www.makemytrip.com/hotels/hotel-listing/?city={encoded}"


class CaratLaneProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "CaratLane"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        encoded = urllib.parse.quote_plus(search_term.strip())
        return f"https://www.caratlane.com/search?q={encoded}"


class MyntraProvider(BaseProductProvider):
    @property
    def platform_name(self) -> str:
        return "Myntra"

    def generate_search_url(self, search_term: str, city: str = "") -> str:
        encoded = urllib.parse.quote_plus(search_term.strip())
        return f"https://www.myntra.com/{encoded}"


class ProductLinkService:
    """Manages search provider routing across different planner domains"""

    def __init__(self):
        self.providers: Dict[str, BaseProductProvider] = {
            "amazon": AmazonProvider(),
            "flipkart": FlipkartProvider(),
            "ikea": IkeaProvider(),
            "swiggy": SwiggyProvider(),
            "zomato": ZomatoProvider(),
            "oyo": OyoProvider(),
            "makemytrip": MakeMyTripProvider(),
            "caratlane": CaratLaneProvider(),
            "myntra": MyntraProvider(),
        }

    def get_links_for_item(
        self,
        item_name: str,
        category: str,
        planner_type: str,
        suggested_platforms: List[str] = None,
        city: str = ""
    ) -> Dict[str, str]:
        """
        Generates valid search URLs for a recommendation item based on its planner type and platforms.
        """
        links: Dict[str, str] = {}
        search_query = item_name

        # Determine platforms to use
        platforms_to_query = []
        if suggested_platforms:
            import re
            for plat in suggested_platforms:
                for sub in re.split(r"[,/]+", str(plat)):
                    cleaned = sub.strip()
                    if cleaned and cleaned not in platforms_to_query:
                        platforms_to_query.append(cleaned)

        cat_lower = category.lower()
        domain_defaults = []
        if planner_type == "party":
            if any(w in cat_lower for w in ["food", "cater", "cake", "beverage", "meal"]):
                domain_defaults = ["Zomato", "Swiggy"]
            elif any(w in cat_lower for w in ["venue", "hotel", "stay", "resort", "hall"]):
                domain_defaults = ["OYO", "MakeMyTrip"]
            else:
                domain_defaults = ["Amazon", "Flipkart"]
        elif planner_type == "home":
            domain_defaults = ["IKEA", "Amazon", "Flipkart"]
        elif planner_type == "jewelry":
            domain_defaults = ["CaratLane", "Myntra", "Amazon"]
        else:
            domain_defaults = ["Amazon", "Flipkart"]

        # Ensure at least one recognized provider exists
        has_valid_provider = any(p.lower().replace(" ", "").replace("-", "") in self.providers for p in platforms_to_query)
        if not has_valid_provider or not platforms_to_query:
            for d in domain_defaults:
                if d not in platforms_to_query:
                    platforms_to_query.append(d)

        for plat in platforms_to_query:
            key = plat.lower().replace(" ", "").replace("-", "")
            provider = self.providers.get(key)
            if provider:
                links[provider.platform_name] = provider.generate_search_url(search_query, city=city)
            else:
                # Fallback to general Amazon search
                links[plat] = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query + ' ' + plat)}"

        return links


product_link_service = ProductLinkService()
