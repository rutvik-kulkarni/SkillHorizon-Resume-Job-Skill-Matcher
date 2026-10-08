import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from course_scraper import scrape_courses_for_skill

print("Testing scraper for 'docker'...")
results = scrape_courses_for_skill("docker")
print(f"Scraper returned {len(results)} results:")
for r in results:
    print(f"- {r['title']} ({r['platform']}) -> {r['url']}")
