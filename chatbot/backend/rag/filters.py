from datetime import datetime

def is_open(metadata):
    now = datetime.now().strftime("%H:%M")

    # Temporary closure
    if metadata.get("temporary_closed"):
        return False

    opening = metadata.get("opening_time")
    closing = metadata.get("closing_time")

    if opening and closing:
        return opening <= now <= closing

    return True


def filter_restaurants(docs):
    filtered = []

    for doc in docs:
        metadata = doc.metadata

        # Only restaurants
        if metadata.get("type") != "restaurant":
            continue

        # Only open ones
        if not is_open(metadata):
            continue

        filtered.append(doc)

    return filtered