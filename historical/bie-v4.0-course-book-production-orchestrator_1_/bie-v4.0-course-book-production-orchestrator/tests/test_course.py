import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from course_orchestrator import prepare_book
def test_course():
 b={"book_id":"b","chapters":[{"lessons":[{"lesson_id":"a","depends_on":[]},{"lesson_id":"b","depends_on":["a"]}]}]}
 r=prepare_book(b)
 assert r["schema_version"]=="4.0"
 assert r["production_queue"]["lesson_order"]==["a","b"]
