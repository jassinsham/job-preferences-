class LearningRecommender:
    def __init__(self):
        # Mapping of common technical skills to curated resources
        self.skill_map = {
            "Python": {
                "why": "The backbone of modern data science and backend engineering.",
                "resources": [
                    {"name": "Official Python Tutorial", "url": "https://docs.python.org/3/tutorial/"},
                    {"name": "Real Python", "url": "https://realpython.com/"}
                ]
            },
            "React": {
                "why": "The most popular library for building modern web interfaces.",
                "resources": [
                    {"name": "React Documentation", "url": "https://react.dev/"},
                    {"name": "Epic React", "url": "https://epicreact.dev/"}
                ]
            },
            "Javascript": {
                "why": "Essential for any web-based development.",
                "resources": [
                    {"name": "MDN Web Docs", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"},
                    {"name": "JavaScript.info", "url": "https://javascript.info/"}
                ]
            },
            "SQL": {
                "why": "Fundamental for interacting with relational databases.",
                "resources": [
                    {"name": "SQLZoo", "url": "https://sqlzoo.net/"},
                    {"name": "Mode SQL Tutorial", "url": "https://mode.com/sql-tutorial/"}
                ]
            },
            "Docker": {
                "why": "The industry standard for application containerization.",
                "resources": [
                    {"name": "Docker Orientation", "url": "https://docs.docker.com/get-started/"},
                    {"name": "Play with Docker", "url": "https://labs.play-with-docker.com/"}
                ]
            },
            "AWS": {
                "why": "The leading cloud platform for hosting scalable applications.",
                "resources": [
                    {"name": "AWS Training", "url": "https://explore.skillbuilder.aws/"},
                    {"name": "A Cloud Guru", "url": "https://acloudguru.com/"}
                ]
            }
        }

    def get_recommendations(self, missing_skills, market_skill_freq=None):
        """
        Returns a list of recommendations for the given missing skills,
        optionally prioritized by market demand frequency.
        """
        recommendations = []
        market_stats = market_skill_freq or {}
        
        # Determine unique missing skills (case-insensitive)
        unique_missing = set([s.lower().strip() for s in missing_skills])
        
        # Build recommendation list
        for skill_name, data in self.skill_map.items():
            if skill_name.lower() in unique_missing:
                # Add market demand score if available
                demand_score = market_stats.get(skill_name.capitalize(), 0)
                
                recommendations.append({
                    "skill": skill_name,
                    "why": data["why"],
                    "resources": data["resources"],
                    "demand_score": demand_score
                })
        
        # Sort by demand score (descending)
        return sorted(recommendations, key=lambda x: x["demand_score"], reverse=True)

    def get_all_skills(self):
        return list(self.skill_map.keys())
