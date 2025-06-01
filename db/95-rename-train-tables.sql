-- rename tables to be prefixed with train

ALTER TABLE AssociatedService RENAME TO TrainAssociatedService;
ALTER TABLE AssociatedType RENAME TO TrainAssociatedServiceType;
ALTER TABLE Brand RENAME TO TrainBrand;
ALTER TABLE Call RENAME TO TrainCall;
ALTER TABLE Leg RENAME TO TrainLeg;
ALTER TABLE LegCall RENAME TO TrainLegCall;
ALTER TABLE Operator RENAME TO TrainOperator;
ALTER TABLE OperatorCode RENAME TO TrainOperatorCode;
ALTER TABLE OperatorStock RENAME TO TrainOperatorStock;
ALTER TABLE Service RENAME TO TrainService;
ALTER TABLE ServiceEndpoint RENAME TO TrainServiceEndpoint;
ALTER TABLE Station RENAME TO TrainStation;
ALTER TABLE StationName RENAME TO TrainStationName;
ALTER TABLE StationPoint RENAME TO TrainStationPoint;
ALTER TABLE Stock RENAME TO TrainStock;
ALTER TABLE StockFormation RENAME TO TrainStockFormation;
ALTER TABLE StockReport RENAME TO TrainStockReport;
ALTER TABLE StockSegment RENAME TO TrainStockSegment;
ALTER TABLE StockSegmentReport RENAME TO TrainStockSegmentReport;
ALTER TABLE StockSubclass RENAME TO TrainStockSubclass;

-- make operator code text

ALTER TABLE TrainOperatorCode ALTER COLUMN operator_code TYPE TEXT;
ALTER TABLE TrainOperatorCode ADD CONSTRAINT trainoperatorcode_check_operator_code CHECK(operator_code ~ '^[[:alpha:]]{2}$');

ALTER TABLE TrainOperator ALTER COLUMN operator_code TYPE TEXT;
ALTER TABLE TrainOperator ADD CONSTRAINT trainoperator_check_operator_code CHECK(operator_code ~ '^[[:alpha:]]{2}$');

ALTER TABLE TrainBrand ALTER COLUMN brand_code TYPE TEXT;
ALTER TABLE TrainBrand ADD CONSTRAINT trainbrand_check_brand_code CHECK(brand_code ~ '^[[:alpha:]]{2}$');

-- make headcode text

ALTER TABLE TrainService ALTER COLUMN headcode TYPE TEXT;
ALTER TABLE TrainService ADD CONSTRAINT headcode_length CHECK (LENGTH(headcode) = 4);

-- alter trainservice primary key

ALTER TABLE TrainServiceEndpoint DROP CONSTRAINT serviceendpoint_service_id_run_date_fkey;
ALTER TABLE TrainCall DROP CONSTRAINT call_service_id_run_date_fkey;
ALTER TABLE TrainAssociatedService DROP CONSTRAINT associatedservice_associated_id_associated_run_date_fkey;

ALTER TABLE TrainService DROP CONSTRAINT service_pkey;
ALTER TABLE TrainService RENAME COLUMN service_id TO unique_identifier;
ALTER TABLE TrainService ADD service_id SERIAL NOT NULL;
ALTER TABLE TrainService ADD CONSTRAINT service_pkey PRIMARY KEY(service_id);
ALTER TABLE TrainService ADD CONSTRAINT service_unique_identifier_run_date_unique UNIQUE (unique_identifier, run_date);

--- at this point, look up the erroneous 25/05/2019 sly to bhm
--- and change its unique identifier to P45344

-- add new foreign key to trainserviceendpoint

ALTER TABLE TrainServiceEndpoint RENAME COLUMN service_id TO unique_identifier;
ALTER TABLE TrainServiceEndpoint ADD service_id INT;

UPDATE TrainServiceEndpoint SET service_id = (
    SELECT TrainService.service_id
    FROM TrainService
    WHERE TrainService.run_date = TrainServiceEndpoint.run_date
    AND TrainService.unique_identifier = TrainServiceEndpoint.unique_identifier
);

ALTER TABLE TrainServiceEndpoint ALTER COLUMN service_id SET NOT NULL;

ALTER TABLE TrainServiceEndpoint
ADD CONSTRAINT trainserviceendpoint_service_id_fkey
FOREIGN KEY(service_id) REFERENCES TrainService(service_id);

ALTER TABLE TrainServiceEndpoint DROP COLUMN unique_identifier;
ALTER TABLE TrainServiceEndpoint DROP COLUMN run_date;

-- add new foreign key to traincall

ALTER TABLE TrainCall RENAME COLUMN service_id TO unique_identifier;
ALTER TABLE TrainCall ADD service_id INT;

UPDATE TrainCall SET service_id = (
    SELECT TrainService.service_id
    FROM TrainService
    WHERE TrainService.run_date = TrainCall.run_date
    AND TrainService.unique_identifier = TrainCall.unique_identifier
);

ALTER TABLE TrainCall ALTER COLUMN service_id SET NOT NULL;

ALTER TABLE TrainCall
ADD CONSTRAINT traincall_service_id_fkey
FOREIGN KEY(service_id) REFERENCES TrainService(service_id);

ALTER TABLE TrainCall DROP COLUMN unique_identifier;
ALTER TABLE TrainCall DROP COLUMN run_date;

-- add new foreign key to trainassociatedservice

ALTER TABLE TrainAssociatedService RENAME COLUMN associated_id TO associated_unique_identifier;
ALTER TABLE TrainAssociatedService ADD associated_service_id INT;

UPDATE TrainAssociatedService SET associated_service_id = (
    SELECT TrainService.service_id
    FROM TrainService
    WHERE TrainService.run_date = TrainAssociatedService.associated_run_date
    AND TrainService.unique_identifier = TrainAssociatedService.associated_unique_identifier
);

ALTER TABLE TrainAssociatedService ALTER COLUMN associated_service_id SET NOT NULL;

ALTER TABLE TrainAssociatedService
ADD CONSTRAINT trainassociatedservice_associated_service_id_fkey
FOREIGN KEY(associated_service_id) REFERENCES TrainService(service_id);

ALTER TABLE TrainAssociatedService DROP COLUMN associated_unique_identifier;
ALTER TABLE TrainAssociatedService DROP COLUMN associated_run_date;

--- make TrainStation.station_crs type text

ALTER TABLE TrainStation ALTER COLUMN station_crs TYPE TEXT;
ALTER TABLE TrainStation ADD CONSTRAINT trainstation_check_station_crs CHECK(station_crs ~ '^[[:alpha:]]{3}$');
ALTER TABLE TrainStation ADD CONSTRAINT trainstation_station_crs_unique UNIQUE(station_crs);

--- make station id primary key

ALTER TABLE TrainStationName DROP CONSTRAINT stationname_station_crs_fkey;
ALTER TABLE TrainStationPoint DROP CONSTRAINT stationpoint_station_crs_fkey;
ALTER TABLE TrainServiceEndpoint DROP CONSTRAINT serviceendpoint_station_crs_fkey;
ALTER TABLE TrainCall DROP CONSTRAINT call_station_crs_fkey;

ALTER TABLE TrainStation DROP CONSTRAINT station_pkey;
ALTER TABLE TrainStation ADD COLUMN station_id SERIAL;
ALTER TABLE TrainStation ADD CONSTRAINT trainstation_pkey PRIMARY KEY(station_id);

---- add new foreign key to TrainStationName

ALTER TABLE TrainStationName ADD station_id INT;

UPDATE TrainStationName SET station_id = (
    SELECT TrainStation.station_id FROM TrainStation
    WHERE TrainStation.station_crs = TrainStationName.station_crs
);

ALTER TABLE TrainStationName ALTER COLUMN station_id SET NOT NULL;

ALTER TABLE TrainStationName
ADD CONSTRAINT trainstationname_station_id_fkey
FOREIGN KEY(station_id) REFERENCES TrainStation(station_id);

ALTER TABLE TrainStationName DROP COLUMN station_crs;

---- add new foreign key to TrainStationPoint

ALTER TABLE TrainStationPoint ADD station_id INT;

UPDATE TrainStationPoint SET station_id = (
    SELECT TrainStation.station_id FROM TrainStation
    WHERE TrainStation.station_crs = TrainStationPoint.station_crs
);

ALTER TABLE TrainStationPoint ALTER COLUMN station_id SET NOT NULL;

ALTER TABLE TrainStationPoint
ADD CONSTRAINT trainstationpoint_station_id_fkey
FOREIGN KEY(station_id) REFERENCES TrainStation(station_id);

ALTER TABLE TrainStationPoint DROP COLUMN station_crs;

---- add new foreign key to TrainServiceEndpoint

ALTER TABLE TrainServiceEndpoint ADD station_id INT;

UPDATE TrainServiceEndpoint SET station_id = (
    SELECT TrainStation.station_id FROM TrainStation
    WHERE TrainStation.station_crs = TrainServiceEndpoint.station_crs
);

ALTER TABLE TrainServiceEndpoint ALTER COLUMN station_id SET NOT NULL;

ALTER TABLE TrainServiceEndpoint
ADD CONSTRAINT trainserviceendpoint_station_id_fkey
FOREIGN KEY(station_id) REFERENCES TrainStation(station_id);

ALTER TABLE TrainServiceEndpoint DROP COLUMN station_crs;

---- add new foreign key to TrainCall

ALTER TABLE TrainCall ADD station_id INT;

UPDATE TrainCall SET station_id = (
    SELECT TrainStation.station_id FROM TrainStation
    WHERE TrainStation.station_crs = TrainCall.station_crs
);

ALTER TABLE TrainCall ALTER COLUMN station_id SET NOT NULL;

ALTER TABLE TrainCall
ADD CONSTRAINT traincall_station_id_fkey
FOREIGN KEY(station_id) REFERENCES TrainStation(station_id);

ALTER TABLE TrainCall DROP COLUMN station_crs;

-- Fix empty stock name

UPDATE TrainStock SET name = NULL WHERE name = '';

-- Readd uniqueness constraint to trainserviceendpoint

ALTER TABLE TrainServiceEndpoint
ADD CONSTRAINT trainserviceendpoint_service_station_origin_unique
UNIQUE (service_id, station_id, origin);

-- Readd uniqueness constraint to trainassociatedservice

ALTER TABLE TrainAssociatedService
ADD CONSTRAINT trainassociatedservice_call_service_type_unique
UNIQUE (call_id, associated_service_id, associated_type);