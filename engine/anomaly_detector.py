def detect_event_time_confusion(event):
    return event["ingestion_time"] < event["event_time"]
def detect_future_leakage(prediction_time, feature_cutoff_time, used_future_data=False):
    return used_future_data or feature_cutoff_time > prediction_time
def detect_delivered_in_transit(status, has_delivery_event):
    return status=="IN_TRANSIT" and has_delivery_event
def detect_impossible_leg_order(sequence_numbers):
    return sequence_numbers != list(range(1,len(sequence_numbers)+1))
