def classify_actual_delivery(actual_delivery_at, promised_delivery_at):
    if actual_delivery_at is None: return "PENDING", 0
    minutes=int((actual_delivery_at-promised_delivery_at).total_seconds()/60)
    return ("DELAYED" if minutes>0 else "ON_TIME", max(0,minutes))
