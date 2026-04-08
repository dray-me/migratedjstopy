def calculate_similarity(str1: str, str2: str) -> float:
    """Calculates the Levenshtein distance between two strings."""
    len1, len2 = len(str1), len(str2)
    if len1 == 0: return 0.0 if len2 > 0 else 1.0
    if len2 == 0: return 0.0
    
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1): matrix[i][0] = i
    for j in range(len2 + 1): matrix[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if str1[i-1] == str2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # Deletion
                matrix[i][j-1] + 1,      # Insertion
                matrix[i-1][j-1] + cost   # Substitution
            )
            
    return 1 - matrix[len1][len2] / max(len1, len2)

def get_similar_commands(command_name: str, commands: list, threshold: float = 0.6) -> list:
    """Returns a list of command names similar to the input string."""
    similar = []
    partial_matches = set()
    
    for cmd in commands:
        # Check primary name
        if command_name in cmd.name or cmd.name in command_name:
            partial_matches.add(cmd.name)
            
        sim = calculate_similarity(command_name, cmd.name)
        if sim >= threshold:
            similar.append({"name": cmd.name, "similarity": sim})
            
        # Check aliases if they exist
        aliases = getattr(cmd, "aliases", [])
        for alias in aliases:
            if command_name in alias or alias in command_name:
                partial_matches.add(alias)
            
            asim = calculate_similarity(command_name, alias)
            if asim >= threshold:
                similar.append({"name": alias, "similarity": asim})
                
    # Sort by similarity descending
    similar.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Combine unique results
    results = list(partial_matches | {s["name"] for s in similar})
    return sorted(results, key=lambda x: next((s["similarity"] for s in similar if s["name"] == x), 0), reverse=True)
