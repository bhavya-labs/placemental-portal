import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

class FeedbackMiner:
    def __init__(self):
        # Fallback dictionary of common themes based on simple word matches
        self.heuristics_themes = {
            "waiting time": "Waiting Time & Scheduling Gaps",
            "delay": "Waiting Time & Scheduling Gaps",
            "schedule": "Waiting Time & Scheduling Gaps",
            "sql": "SQL Query & Database Design Round",
            "database": "SQL Query & Database Design Round",
            "recursion": "DSA - Recursion and Backtracking",
            "pointer": "C/C++ Pointer Mechanics",
            "resume": "Resume Formatting & Screening Match",
            "ats": "Resume Formatting & Screening Match",
            "difficult": "Technical Interview Difficulty",
            "hard": "Technical Interview Difficulty",
            "trainer": "Trainer Explanation Quality",
            "explain": "Trainer Explanation Quality"
        }

    def group_feedback(self, feedbacks: List[Any]) -> List[Dict[str, Any]]:
        """
        Group feedback objects semantically based on TF-IDF cosine similarity.
        """
        if not feedbacks:
            return []

        texts = [f.experience_text for f in feedbacks]
        if len(texts) < 2:
            # Single feedback, return as one theme
            f = feedbacks[0]
            theme_name = self._detect_theme_heuristic(f.experience_text)
            return [{
                "theme": theme_name,
                "student_count": 1,
                "average_rating": f.rating or 3.0,
                "consolidated_explanation": f"A student reported about: {f.experience_text[:120]}...",
                "supporting_points": [f.experience_text],
                "suggestions": [f.suggestions] if f.suggestions else [],
                "original_feedbacks": [{
                    "id": f.id,
                    "experience_text": f.experience_text,
                    "suggestions": f.suggestions,
                    "rating": f.rating
                }]
            }]

        # Run Vectorization
        try:
            # Normalize texts (strip, lowercase)
            normalized_texts = [t.strip().lower() for t in texts]
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(normalized_texts)
            sim_matrix = cosine_similarity(tfidf_matrix)
        except Exception:
            # Fallback in case vectorizer fails on empty words
            sim_matrix = np.eye(len(texts))

        # Perform simple single-linkage clustering / grouping
        visited = set()
        groups = []

        for i in range(len(texts)):
            if i in visited:
                continue
            
            # Start a new group
            group_indices = [i]
            visited.add(i)

            rating_i = feedbacks[i].rating or feedbacks[i].difficulty_rating or 3
            sentiment_i = feedbacks[i].sentiment_score or 0.0

            for j in range(i + 1, len(texts)):
                if j not in visited:
                    rating_j = feedbacks[j].rating or feedbacks[j].difficulty_rating or 3
                    sentiment_j = feedbacks[j].sentiment_score or 0.0
                    
                    # Avoid merging contradictory opinions (e.g. large rating gap or positive vs negative sentiment)
                    is_contradictory = (
                        (rating_i >= 4 and rating_j <= 2) or
                        (rating_i <= 2 and rating_j >= 4) or
                        (sentiment_i > 0.15 and sentiment_j < -0.15) or
                        (sentiment_i < -0.15 and sentiment_j > 0.15)
                    )
                    
                    if not is_contradictory and sim_matrix[i, j] >= 0.35:
                        group_indices.append(j)
                        visited.add(j)

            groups.append(group_indices)

        # Build theme summaries for each group
        mined_themes = []
        for g_indices in groups:
            group_fbs = [feedbacks[idx] for idx in g_indices]
            avg_rating = float(np.mean([f.rating or 3.0 for f in group_fbs]))
            avg_difficulty = float(np.mean([f.difficulty_rating or 3 for f in group_fbs]))
            
            # Detect theme name based on majority vote or heuristics
            theme_counts = {}
            for f in group_fbs:
                theme_detected = self._detect_theme_heuristic(f.experience_text)
                theme_counts[theme_detected] = theme_counts.get(theme_detected, 0) + 1
            theme_name = max(theme_counts, key=theme_counts.get)

            # Build consolidated summary
            quotes = [f.experience_text for f in group_fbs]
            suggestions = [f.suggestions for f in group_fbs if f.suggestions]

            # Generate smart consolidated description
            pos_words = ["good", "clear", "helpful", "smooth", "explained well"]
            neg_words = ["long", "waiting", "delayed", "hard", "difficult", "struggled"]
            
            has_pos = any(any(pw in q.lower() for pw in pos_words) for q in quotes)
            has_neg = any(any(nw in q.lower() for nw in neg_words) for q in quotes)

            if has_pos and has_neg:
                explanation = f"Students had mixed experiences regarding this theme. While some appreciated the core delivery, others highlighted operational difficulties."
            elif has_neg:
                explanation = f"Students reported concerns and bottlenecks regarding {theme_name.lower()}. They noted specific operational issues and delays."
            else:
                explanation = f"Students shared highly positive feedback about this theme, praising the clear instructions and supportive environment."

            original_list = [{
                "id": f.id,
                "experience_text": f.experience_text,
                "suggestions": f.suggestions,
                "rating": f.rating
            } for f in group_fbs]

            mined_themes.append({
                "theme": theme_name,
                "student_count": len(group_fbs),
                "average_rating": round(avg_rating, 2),
                "average_difficulty": round(avg_difficulty, 2),
                "consolidated_explanation": explanation,
                "supporting_points": quotes[:3], # Show top 3 quotes
                "suggestions": list(set(suggestions))[:3],
                "original_feedbacks": original_list
            })

        # Sort themes by student count desc
        return sorted(mined_themes, key=lambda x: x["student_count"], reverse=True)

    def _detect_theme_heuristic(self, text: str) -> str:
        text_lower = text.lower()
        for kw, theme in self.heuristics_themes.items():
            if kw in text_lower:
                return theme
        return "General Interview Experience"

feedback_miner = FeedbackMiner()
