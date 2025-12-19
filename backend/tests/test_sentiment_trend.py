import sys
sys.path.append('.')

from models.database import get_engine, Brand, Mention
from sqlmodel import Session, select,func
from sqlalchemy import case
from datetime import datetime, timedelta

# Create session
database_url = "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
engine = get_engine(database_url)
session = Session(engine)

# Test query
brand_id = 2
days = 30

end_date = datetime.utcnow()
start_date = end_date - timedelta(days=days)

try:
    statement = select(
        func.date(Mention.published_date).label("date"),
        func.avg(Mention.sentiment_score).label("avg_score"),
        func.count(Mention.id).label("mention_count"),
        func.sum(case((Mention.sentiment_label == "Positive", 1), else_=0)).label("positive_count"),
        func.sum(case((Mention.sentiment_label == "Neutral", 1), else_=0)).label("neutral_count"),
        func.sum(case((Mention.sentiment_label == "Negative", 1), else_=0)).label("negative_count")
    ).where(
        Mention.brand_id == brand_id,
        Mention.published_date >= start_date,
        Mention.published_date <= end_date,
        Mention.sentiment_score.isnot(None)
    ).group_by(
        func.date(Mention.published_date)
    ).order_by(
        func.date(Mention.published_date)
    )

    results = session.exec(statement).all()
    print(f"Query successful! Found {len(results)} results")
    for row in results:
        print(f"Date: {row.date}, Avg: {row.avg_score}, Count: {row.mention_count}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

session.close()
