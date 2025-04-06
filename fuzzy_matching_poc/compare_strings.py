from thefuzz import fuzz, process

def fuzzy_match(query, choices, threshold=50):
    """
    Perform fuzzy string matching between a query and a list of choices.
    
    Parameters:
    query (str): The string to match against
    choices (list): List of strings to search through
    threshold (int): Minimum similarity score (0-100) to consider a match
    
    Returns:
    list: Matching results above threshold, sorted by score
    """
    # Get all matches with their scores
    matches = process.extract(query, choices, scorer=fuzz.ratio)
    
    # Print all scores before filtering
    print("\nAll scores before filtering:")
    for match, score in matches:
        print(f"{match}: {score}")
    
    # Filter matches above threshold and sort by score
    good_matches = [(match, score) for match, score in matches if score >= threshold]
    return sorted(good_matches, key=lambda x: x[1], reverse=True)

def demonstrate_fuzzy_matching():
    # Sample data
    company_names = [
        "Apple Inc.",
        "Apple Computer",
        "Apple Corp",
        "Microsoft Corporation",
        "Amazon.com Inc",
        "Meta Platforms",
        "Alphabet Inc."
    ]
    
    # Different fuzzy matching methods
    query = "apple company"
    
    # Simple ratio
    print("Simple Ratio Matches:")
    for name in company_names:
        score = fuzz.ratio(query.lower(), name.lower())
        print(f"{name}: {score}")
    
    # Partial ratio (better for substrings)
    print("\nPartial Ratio Matches:")
    for name in company_names:
        score = fuzz.partial_ratio(query.lower(), name.lower())
        print(f"{name}: {score}")
    
    # Token sort ratio (better for word order differences)
    print("\nToken Sort Ratio Matches:")
    for name in company_names:
        score = fuzz.token_sort_ratio(query.lower(), name.lower())
        print(f"{name}: {score}")
    
    threshold = 70
    # Using the fuzzy_match function
    print(f"\nFuzzy Match Results (threshold={threshold}):")
    matches = fuzzy_match(query, company_names, threshold)
    print("\nFiltered matches:")
    for match, score in matches:
        print(f"{match}: {score}")

if __name__ == "__main__":
    demonstrate_fuzzy_matching()