def calculate_match_score(user1_skills, user1_interests, user1_looking_for, 
                          user2_skills, user2_interests, user2_looking_for):
    """
    Computes a compatibility score based on:
    40% Skill Overlap
    30% Interest Overlap
    30% Collaboration Intent (Looking For) Overlap
    """
    
    def calculate_overlap_percentage(list1, list2):
        if not list1 and not list2:
            return 0.0 # Both empty means no overlap context
        
        set1 = set(list1)
        set2 = set(list2)
        
        # We calculate overlap relative to the smaller set.  
        # E.g., if User A knows Python, and User B knows Python + Java + C++, 
        # they have 100% overlap from User A's perspective.
        overlap = len(set1.intersection(set2))
        smaller_list_size = min(len(set1), len(set2))
        
        if smaller_list_size == 0:
             return 0.0
             
        return (overlap / smaller_list_size) * 100.0

    skill_score = calculate_overlap_percentage(user1_skills, user2_skills)
    interest_score = calculate_overlap_percentage(user1_interests, user2_interests)
    intent_score = calculate_overlap_percentage(user1_looking_for, user2_looking_for)
    
    # Apply weights
    total_score = (skill_score * 0.40) + (interest_score * 0.30) + (intent_score * 0.30)
    
    return round(total_score)

def get_top_matches(current_user_email, all_profiles, all_skills, all_interests, all_looking_for):
    """
    Returns a list of dictionaries containing calculated match scores for all other valid users.
    Output: [{"email": "...", "score": 85, "overlapping_skills": [...], "overlapping_interests": [...]}]
    """
    if current_user_email not in all_profiles:
        return []
        
    my_skills = all_skills.get(current_user_email, [])
    my_interests = all_interests.get(current_user_email, [])
    my_looking = all_looking_for.get(current_user_email, [])
    
    matches = []
    
    for other_email, other_profile in all_profiles.items():
        if other_email == current_user_email:
            continue
            
        their_skills = all_skills.get(other_email, [])
        their_interests = all_interests.get(other_email, [])
        their_looking = all_looking_for.get(other_email, [])
        
        score = calculate_match_score(
            my_skills, my_interests, my_looking,
            their_skills, their_interests, their_looking
        )
        
        # Find exact overlapping strings for UI display
        overlap_skills = list(set(my_skills).intersection(set(their_skills)))
        overlap_interests = list(set(my_interests).intersection(set(their_interests)))
        
        matches.append({
            "email": other_email,
            "name": other_profile.get("full_name", other_email.split('@')[0].capitalize()),
            "score": score,
            "overlapping_skills": overlap_skills,
            "overlapping_interests": overlap_interests,
            "skills": their_skills, # Full skill set for context
            "interests": their_interests
        })
        
    # Sort descending by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches
