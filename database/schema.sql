CREATE DATABASE IF NOT EXISTS shipsense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE shipsense;

CREATE TABLE IF NOT EXISTS carriers (
 carrier_id VARCHAR(30) PRIMARY KEY, carrier_name VARCHAR(120) NOT NULL,
 service_type ENUM('ROAD','AIR','RAIL','SEA','MULTIMODAL') NOT NULL,
 reliability_score DECIMAL(5,2) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS facilities (
 facility_id VARCHAR(30) PRIMARY KEY, facility_name VARCHAR(120) NOT NULL,
 city VARCHAR(80) NOT NULL, state VARCHAR(80) NOT NULL, region VARCHAR(40) NOT NULL,
 capacity_per_hour INT NOT NULL, operating_start TIME NOT NULL, operating_end TIME NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS service_levels (
 service_level_id VARCHAR(30) PRIMARY KEY, service_name VARCHAR(80) NOT NULL,
 sla_hours INT NOT NULL, priority INT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS routes (
 route_id VARCHAR(30) PRIMARY KEY, origin_facility_id VARCHAR(30) NOT NULL,
 destination_facility_id VARCHAR(30) NOT NULL, distance_km DECIMAL(10,2) NOT NULL,
 base_transit_hours DECIMAL(8,2) NOT NULL,
 FOREIGN KEY (origin_facility_id) REFERENCES facilities(facility_id),
 FOREIGN KEY (destination_facility_id) REFERENCES facilities(facility_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS shipments (
 shipment_id VARCHAR(30) PRIMARY KEY, carrier_id VARCHAR(30) NOT NULL,
 service_level_id VARCHAR(30) NOT NULL, origin_facility_id VARCHAR(30) NOT NULL,
 destination_facility_id VARCHAR(30) NOT NULL, created_at DATETIME NOT NULL,
 promised_delivery_at DATETIME NOT NULL, actual_delivery_at DATETIME NULL,
 status ENUM('CREATED','PICKED_UP','IN_TRANSIT','OUT_FOR_DELIVERY','DELIVERED','DELAYED','EXCEPTION','CANCELLED') NOT NULL,
 total_distance_km DECIMAL(10,2) NOT NULL, issue_type VARCHAR(60) NULL,
 FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
 FOREIGN KEY (service_level_id) REFERENCES service_levels(service_level_id),
 FOREIGN KEY (origin_facility_id) REFERENCES facilities(facility_id),
 FOREIGN KEY (destination_facility_id) REFERENCES facilities(facility_id),
 INDEX idx_shipments_status(status), INDEX idx_shipments_promised(promised_delivery_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS shipment_legs (
 leg_id VARCHAR(60) PRIMARY KEY, shipment_id VARCHAR(30) NOT NULL,
 route_id VARCHAR(30) NOT NULL, carrier_id VARCHAR(30) NOT NULL,
 sequence_no INT NOT NULL, planned_departure_at DATETIME NOT NULL,
 planned_arrival_at DATETIME NOT NULL, actual_departure_at DATETIME NULL,
 actual_arrival_at DATETIME NULL, leg_status VARCHAR(30) NOT NULL,
 FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
 FOREIGN KEY (route_id) REFERENCES routes(route_id),
 FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
 UNIQUE KEY uq_shipment_leg_sequence(shipment_id, sequence_no)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tracking_events (
 event_id VARCHAR(60) PRIMARY KEY, shipment_id VARCHAR(30) NOT NULL,
 leg_id VARCHAR(60) NULL, carrier_id VARCHAR(30) NOT NULL,
 event_type VARCHAR(40) NOT NULL, event_location VARCHAR(120) NOT NULL,
 event_time DATETIME NOT NULL, ingestion_time DATETIME NOT NULL,
 source_system VARCHAR(50) NOT NULL, is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
 issue_type VARCHAR(60) NULL,
 FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
 FOREIGN KEY (leg_id) REFERENCES shipment_legs(leg_id),
 FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
 INDEX idx_event_shipment_time(shipment_id,event_time),
 INDEX idx_event_ingestion(ingestion_time)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS facility_queues (
 queue_id VARCHAR(60) PRIMARY KEY, facility_id VARCHAR(30) NOT NULL,
 queue_time DATETIME NOT NULL, queue_length INT NOT NULL,
 processing_capacity INT NOT NULL, average_processing_minutes DECIMAL(8,2) NOT NULL,
 estimated_wait_minutes DECIMAL(8,2) NOT NULL,
 FOREIGN KEY (facility_id) REFERENCES facilities(facility_id),
 INDEX idx_queue_facility_time(facility_id,queue_time)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS weather_events (
 weather_event_id VARCHAR(40) PRIMARY KEY, region VARCHAR(40) NOT NULL,
 weather_type VARCHAR(40) NOT NULL, severity ENUM('LOW','MODERATE','HIGH','SEVERE') NOT NULL,
 start_time DATETIME NOT NULL, end_time DATETIME NOT NULL,
 travel_impact_minutes INT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS route_weather_impacts (
 route_id VARCHAR(30) NOT NULL, weather_event_id VARCHAR(40) NOT NULL,
 PRIMARY KEY(route_id,weather_event_id),
 FOREIGN KEY(route_id) REFERENCES routes(route_id),
 FOREIGN KEY(weather_event_id) REFERENCES weather_events(weather_event_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS eta_estimates (
 eta_id VARCHAR(100) PRIMARY KEY, shipment_id VARCHAR(30) NOT NULL,
 prediction_time DATETIME NOT NULL, feature_cutoff_time DATETIME NOT NULL,
 baseline_eta DATETIME NOT NULL, predicted_eta DATETIME NOT NULL,
 predicted_delay_minutes INT NOT NULL, risk_level ENUM('LOW','MEDIUM','HIGH') NOT NULL,
 weather_adjustment_minutes INT NOT NULL, facility_adjustment_minutes INT NOT NULL,
 route_adjustment_minutes INT NOT NULL, carrier_adjustment_minutes INT NOT NULL,
 eligible_event_count INT NOT NULL DEFAULT 0,
 rule_version VARCHAR(30) NOT NULL, used_future_data BOOLEAN NOT NULL DEFAULT FALSE,
 UNIQUE KEY uq_eta_snapshot(shipment_id,prediction_time),
 CHECK (feature_cutoff_time <= prediction_time),
 CHECK (predicted_eta >= baseline_eta),
 CHECK (predicted_delay_minutes >= 0),
 CHECK (weather_adjustment_minutes >= 0 AND facility_adjustment_minutes >= 0
    AND route_adjustment_minutes >= 0 AND carrier_adjustment_minutes >= 0),
 FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id),
 INDEX idx_eta_shipment_time(shipment_id,prediction_time)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS delay_reasons (
 delay_reason_id VARCHAR(30) PRIMARY KEY, reason_code VARCHAR(40) NOT NULL UNIQUE,
 description VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS shipment_delay_assessments (
 assessment_id VARCHAR(40) PRIMARY KEY, shipment_id VARCHAR(30) NOT NULL,
 delay_reason_id VARCHAR(30) NULL, actual_delay_minutes INT NOT NULL,
 outcome VARCHAR(20) NOT NULL, assessed_at DATETIME NOT NULL,
 FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id),
 FOREIGN KEY(delay_reason_id) REFERENCES delay_reasons(delay_reason_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS shipment_status_history (
 history_id VARCHAR(50) PRIMARY KEY, shipment_id VARCHAR(30) NOT NULL,
 previous_status VARCHAR(30) NULL, new_status VARCHAR(30) NOT NULL,
 changed_at DATETIME NOT NULL, source_event_id VARCHAR(60) NULL,
 FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id),
 FOREIGN KEY(source_event_id) REFERENCES tracking_events(event_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS data_quality_issues (
 issue_id VARCHAR(50) PRIMARY KEY, shipment_id VARCHAR(30) NOT NULL,
 record_id VARCHAR(100) NOT NULL, issue_type VARCHAR(60) NOT NULL,
 severity VARCHAR(20) NOT NULL, detected_at DATETIME NOT NULL,
 description VARCHAR(255) NOT NULL,
 FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id),
 INDEX idx_issue_type(issue_type)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS generation_runs (
 run_id VARCHAR(40) PRIMARY KEY, seed_value BIGINT NOT NULL,
 dataset_size VARCHAR(20) NOT NULL, shipment_count INT NOT NULL,
 event_count INT NOT NULL, generated_at DATETIME NOT NULL,
 manifest_json JSON NOT NULL
) ENGINE=InnoDB;


-- Effective-dated carrier operating / service calendars.
CREATE TABLE IF NOT EXISTS carrier_calendars (
 calendar_id VARCHAR(40) PRIMARY KEY, carrier_id VARCHAR(30) NOT NULL,
 effective_from DATETIME NOT NULL, effective_to DATETIME NOT NULL,
 adjustment_minutes INT NOT NULL DEFAULT 0, reason VARCHAR(255) NOT NULL,
 CHECK (effective_to > effective_from), CHECK (adjustment_minutes >= 0),
 FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
 INDEX idx_carrier_calendar_effective(carrier_id,effective_from,effective_to)
) ENGINE=InnoDB;

-- Facility disruption windows are distinct from instantaneous queue snapshots.
CREATE TABLE IF NOT EXISTS facility_disruptions (
 disruption_id VARCHAR(40) PRIMARY KEY, facility_id VARCHAR(30) NOT NULL,
 start_time DATETIME NOT NULL, end_time DATETIME NOT NULL,
 disruption_type ENUM('CAPACITY_REDUCTION','CLOSURE','MAINTENANCE','WEATHER') NOT NULL,
 disruption_minutes INT NOT NULL, description VARCHAR(255) NOT NULL,
 CHECK (end_time > start_time), CHECK (disruption_minutes >= 0),
 FOREIGN KEY (facility_id) REFERENCES facilities(facility_id),
 INDEX idx_facility_disruption_window(facility_id,start_time,end_time)
) ENGINE=InnoDB;

-- Append-only route revision history. effective_at controls point-in-time visibility.
CREATE TABLE IF NOT EXISTS route_change_history (
 route_change_id VARCHAR(60) PRIMARY KEY, shipment_id VARCHAR(30) NOT NULL,
 old_route_id VARCHAR(30) NOT NULL, new_route_id VARCHAR(30) NOT NULL,
 effective_at DATETIME NOT NULL, transit_adjustment_minutes INT NOT NULL,
 change_reason ENUM('WEATHER_REROUTE','FACILITY_CLOSURE','CARRIER_CHANGE','PLANNING_UPDATE') NOT NULL,
 ground_truth_label VARCHAR(30) NOT NULL,
 CHECK (old_route_id <> new_route_id),
 FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
 FOREIGN KEY (old_route_id) REFERENCES routes(route_id),
 FOREIGN KEY (new_route_id) REFERENCES routes(route_id),
 INDEX idx_route_change_shipment_time(shipment_id,effective_at)
) ENGINE=InnoDB;

-- ETA estimates are immutable snapshots; a shipment may have many snapshots.
