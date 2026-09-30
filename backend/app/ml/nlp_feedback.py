import re
from typing import List, Dict, Any, Tuple

class FeedbackNLPAnalyzer:
    def __init__(self):
        # Lexicons for sentiment analysis
        self.positive_words = {
            "easy", "friendly", "helpful", "supportive", "encouraging", "good", "great", 
            "excellent", "comfortable", "smooth", "polite", "solved", "cleared", "selected", 
            "nice", "positive", "warm", "appreciated", "fair", "clear", "helpful", "relaxed"
        }
        self.negative_words = {
            "difficult", "hard", "stressful", "tough", "rude", "harsh", "rejected", "failed", 
            "unhelpful", "confusing", "anxious", "nervous", "complicated", "gridlocked", "stuck", 
            "negative", "intimidating", "rigid", "disappointed", "cold", "rushed", "incomplete"
        }

        # Buzzwords mapping for keyword extraction
        self.tech_keywords = [
            "SQL", "Java", "Python", "C++", "C#", "JavaScript", "React", "Node", "Angular", 
            "DBMS", "Operating Systems", "OS", "Computer Networks", "CN", "Data Structures", 
            "DSA", "Algorithms", "Dynamic Programming", "Recursion", "OOPs", "System Design", 
            "HTML", "CSS", "Docker", "Kubernetes", "AWS", "Git", "Machine Learning", "ML", 
            "Pointers", "Inheritance", "Polymorphism", "Indexes", "Joins", "Normalization"
        ]

        # Topic categorization rules
        self.topic_mapping = {
            "Data Structures & Algorithms": ["dsa", "data structures", "algorithms", "array", "tree", "graph", "recursion", "dynamic programming", "pointers", "binary", "list"],
            "Database Management Systems": ["dbms", "sql", "database", "joins", "normalization", "index", "queries", "transactions"],
            "Object-Oriented Programming": ["oops", "object", "class", "inheritance", "polymorphism", "encapsulation", "abstraction", "java", "c++"],
            "Web Development": ["react", "node", "javascript", "html", "css", "angular", "frontend", "backend", "fullstack", "api"],
            "System Design & Cloud": ["system design", "aws", "docker", "kubernetes", "cloud", "scaling", "microservices"],
            "Core CS (OS & Networks)": ["os", "operating system", "networks", "cn", "tcp", "ip", "thread", "process", "memory"]
        }

    def clean_text(self, text: str) -> str:
        """Lowercases and cleans special characters from text."""
        if not text:
            return ""
        text = text.lower()
        # Remove special characters except alphanumeric and whitespace
        text = re.sub(r"[^\w\s]", " ", text)
        return text

    def analyze_sentiment(self, text: str) -> float:
        """
        Calculate sentiment score from -1.0 to 1.0 based on lexical matching.
        """
        cleaned = self.clean_text(text)
        words = cleaned.split()
        if not words:
            return 0.0

        pos_count = 0
        neg_count = 0
        for w in words:
            if w in self.positive_words:
                pos_count += 1
            elif w in self.negative_words:
                neg_count += 1

        total_sentiment_words = pos_count + neg_count
        if total_sentiment_words == 0:
            return 0.0

        # Returns score between -1 and 1
        score = (pos_count - neg_count) / total_sentiment_words
        return float(round(score, 2))

    def extract_keywords(self, text: str) -> List[str]:
        """
        Identify standard technical keywords present in the text.
        """
        extracted = []
        for kw in self.tech_keywords:
            # Word boundary regex to avoid substring matches (e.g. "C" in "Coding")
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, text.lower()):
                extracted.append(kw)
        return extracted

    def identify_topic(self, text: str) -> str:
        """
        Categorize the interview feedback text into a core subject area.
        """
        cleaned = self.clean_text(text)
        scores = {topic: 0 for topic in self.topic_mapping}

        for topic, keywords in self.topic_mapping.items():
            for kw in keywords:
                # Find matching occurrences of keyword
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = re.findall(pattern, cleaned)
                scores[topic] += len(matches)

        # Get topic with maximum matches
        max_topic = max(scores, key=scores.get)
        if scores[max_topic] == 0:
            return "General / Behavioral"
        return max_topic

    def process_feedback(self, text: str) -> Dict[str, Any]:
        """
        Runs sentiment analysis, keyword extraction, and topic analysis in one pass.
        """
        sentiment = self.analyze_sentiment(text)
        keywords = self.extract_keywords(text)
        topic = self.identify_topic(text)

        return {
            "sentiment_score": sentiment,
            "extracted_keywords": ", ".join(keywords),
            "topic_analysis": topic
        }

nlp_analyzer = FeedbackNLPAnalyzer()
