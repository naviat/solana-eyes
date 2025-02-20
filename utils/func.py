def update_metric(metric, value, labels=None):
    """
    Update Prometheus metric with optional labels.
    
    Args:
        metric: Prometheus metric object
        value: Value to set
        labels: Optional dictionary of label key-value pairs
    """
    if value is not None:
        if labels:
            metric.labels(**labels).set(value)
        else:
            metric.set(value)
