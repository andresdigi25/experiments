from thefuzz import fuzz, process
import re
import usaddress

class AddressMatcher:
    def __init__(self):
        """Initialize the address matcher with common abbreviations and cleaners."""
        self.street_type_mapping = {
            'ST': 'STREET',
            'RD': 'ROAD',
            'DR': 'DRIVE',
            'LN': 'LANE',
            'AVE': 'AVENUE',
            'BLVD': 'BOULEVARD',
            'CTR': 'CENTER',
            'CIR': 'CIRCLE',
            'CT': 'COURT',
            'PL': 'PLACE',
            'SQ': 'SQUARE',
            'TER': 'TERRACE',
            'PKY': 'PARKWAY',
            'PKWY': 'PARKWAY',
            'HWY': 'HIGHWAY'
        }
        
        self.direction_mapping = {
            'N': 'NORTH',
            'S': 'SOUTH',
            'E': 'EAST',
            'W': 'WEST',
            'NE': 'NORTHEAST',
            'NW': 'NORTHWEST',
            'SE': 'SOUTHEAST',
            'SW': 'SOUTHWEST'
        }

    def standardize_address(self, address):
        """
        Standardize address format by expanding abbreviations and removing special characters.
        """
        if not address:
            return ""
            
        # Convert to uppercase
        address = address.upper()
        
        # Parse address using usaddress library
        try:
            parsed_addr, addr_type = usaddress.tag(address)
        except:
            return address
            
        # Expand street type abbreviations
        for abbr, full in self.street_type_mapping.items():
            address = re.sub(r'\b' + abbr + r'\b', full, address)
            
        # Expand directional abbreviations
        for abbr, full in self.direction_mapping.items():
            address = re.sub(r'\b' + abbr + r'\b', full, address)
            
        # Remove special characters and extra spaces
        address = re.sub(r'[^\w\s]', ' ', address)
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address

    def compare_addresses(self, addr1, addr2):
        """
        Compare two addresses and return similarity scores using different methods.
        """
        # Standardize both addresses
        std_addr1 = self.standardize_address(addr1)
        std_addr2 = self.standardize_address(addr2)
        
        # Calculate different similarity scores
        scores = {
            'ratio': fuzz.ratio(std_addr1, std_addr2),
            'partial_ratio': fuzz.partial_ratio(std_addr1, std_addr2),
            'token_sort_ratio': fuzz.token_sort_ratio(std_addr1, std_addr2),
            'token_set_ratio': fuzz.token_set_ratio(std_addr1, std_addr2)
        }
        
        return scores

    def find_matches(self, query_address, address_list, threshold=80):
        """
        Find matching addresses from a list that exceed the similarity threshold.
        
        Returns list of tuples (address, score, match_type)
        """
        matches = []
        std_query = self.standardize_address(query_address)
        
        for addr in address_list:
            scores = self.compare_addresses(query_address, addr)
            
            # Get the best score and its type
            best_score = max(scores.values())
            best_match_type = max(scores.items(), key=lambda x: x[1])[0]
            
            if best_score >= threshold:
                matches.append((addr, best_score, best_match_type))
                
        return sorted(matches, key=lambda x: x[1], reverse=True)

def demonstrate_address_matching():
    # Sample addresses
    addresses = [
        "123 Main Street, New York, NY 10001",
        "123 Main St, New York, NY 10001",
        "123 Main Street N, New York, NY 10001",
        "123 Main Street North, New York, NY 10001",
        "124 Main Street, New York, NY 10001",
        "123 Maine St, New York, NY 10001",
        "123 Main Street Suite 4B, New York, NY 10001"
    ]
    
    # Create matcher instance
    matcher = AddressMatcher()
    
    # Test with slightly misspelled address
    query = "pinga 345, New York, NY 10001"
    print(f"\nSearching for matches for: {query}")
    
    matches = matcher.find_matches(query, addresses)
    
    print("\nMatches found:")
    for addr, score, match_type in matches:
        print(f"Address: {addr}")
        print(f"Score: {score}")
        print(f"Match Type: {match_type}")
        print("-" * 50)

if __name__ == "__main__":
    demonstrate_address_matching()